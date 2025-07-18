import os
import json
import uuid
import datetime
import time
import shutil
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import glob
import re

from indextts.infer import IndexTTS

app = Flask(__name__)

# 配置文件路径
CONFIG_FILE = "config.json"

# 生成记录文件路径
HISTORY_FILE = "records/generation_history.json"

# 添加字体目录配置
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'font')

# 添加新的语音目录配置
VOICE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'voice')
VOICE_CATEGORIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'voice_categories.json')

# 临时目录配置
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')

# 确保记录目录存在
os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
# 确保语音目录存在
os.makedirs(VOICE_DIR, exist_ok=True)
# 确保临时目录存在
os.makedirs(TEMP_DIR, exist_ok=True)

# 加载语音分类数据
def load_voice_categories():
    # 获取所有子目录作为分类
    subdirs = [d for d in os.listdir(VOICE_DIR) 
               if os.path.isdir(os.path.join(VOICE_DIR, d)) and d not in ['.', '..']]
    
    # 创建基础分类列表
    categories = {
        "categories": []
    }
    
    # 添加默认基础分类
    default_categories = []
    
    # 确保基础分类存在
    for category in default_categories:
        if category["id"] not in subdirs:
            subdirs.append(category["id"])
        categories["categories"].append(category)
    
    # 添加其他发现的目录作为分类
    for dir_name in subdirs:
        # 检查是否已经在基础分类中
        if not any(cat["id"] == dir_name for cat in categories["categories"]):
            # 添加新分类
            categories["categories"].append({
                "id": dir_name,
                "name": dir_name.capitalize(),  # 首字母大写作为默认名称
                "description": f"{dir_name.capitalize()}分类"
            })
            app.logger.info(f"自动添加新分类: {dir_name}")
    
    # 确保所有分类都有对应的目录
    for category in categories["categories"]:
        cat_dir = os.path.join(VOICE_DIR, category["id"])
        if not os.path.exists(cat_dir):
            os.makedirs(cat_dir)
            app.logger.info(f"为分类 {category['id']} 创建目录")
    
    # 保存分类信息到文件
    save_voice_categories(categories)
    
    return categories

# 保存语音分类数据
def save_voice_categories(categories):
    with open(VOICE_CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)

# 更新语音分类 - 移动音频文件到对应分类目录
def update_voice_category(voice_name, category_id):
    # 查找音频文件
    file_path = None
    current_category = None
    
    for root, dirs, files in os.walk(VOICE_DIR):
        if voice_name in files:
            file_path = os.path.join(root, voice_name)
            # 获取当前分类（相对路径）
            current_category = os.path.relpath(root, VOICE_DIR)
            if current_category == '.':
                current_category = 'other'
            break
    
    if not file_path:
        return False
    
    # 如果已经在正确的分类中，不需要移动
    if current_category == category_id:
        return True
    
    # 目标目录
    target_dir = os.path.join(VOICE_DIR, category_id)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # 目标文件路径
    target_path = os.path.join(target_dir, voice_name)
    
    # 如果目标文件已存在，添加时间戳避免冲突
    if os.path.exists(target_path) and file_path != target_path:
        name, ext = os.path.splitext(voice_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        new_name = f"{name}_{timestamp}{ext}"
        target_path = os.path.join(target_dir, new_name)
        
        # 更新voice_name为新名称
        voice_name = new_name
    
    # 移动文件
    try:
        shutil.move(file_path, target_path)
        app.logger.info(f"已将音频 {voice_name} 从 {current_category} 移动到 {category_id}")
        
        # 更新data.json
        voice_data, data_file = load_voice_data()
        
        # 更新或添加音频信息
        voice_url = f"voice/{category_id}/{voice_name}"
        if voice_name in voice_data:
            voice_data[voice_name]["path"] = voice_url
            voice_data[voice_name]["category"] = category_id
        else:
            voice_data[voice_name] = {
                "note": "",
                "path": voice_url,
                "category": category_id
            }
        
        # 保存更新
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(voice_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        app.logger.error(f"移动音频文件失败: {str(e)}")
        return False

# 添加新的语音分类
def add_voice_category(category_id, category_name, description=""):
    categories = load_voice_categories()
    
    # 检查是否已存在
    for category in categories["categories"]:
        if category["id"] == category_id:
            return False, "分类ID已存在"
    
    # 添加新分类
    categories["categories"].append({
        "id": category_id,
        "name": category_name,
        "description": description
    })
    
    # 创建目录
    category_path = os.path.join(VOICE_DIR, category_id)
    os.makedirs(category_path, exist_ok=True)
    
    save_voice_categories(categories)
    
    return True, "分类添加成功"

# 删除语音分类
def delete_voice_category(category_id):
    categories = load_voice_categories()
    # 查找并移除分类
    categories["categories"] = [cat for cat in categories["categories"] if cat["id"] != category_id]
    # 保存更新
    save_voice_categories(categories)
    # 删除分类目录下的所有音频文件和目录本身
    source_dir = os.path.join(VOICE_DIR, category_id)
    if os.path.exists(source_dir):
        for file in os.listdir(source_dir):
            if file.endswith((".wav", ".mp3")):
                source_file = os.path.join(source_dir, file)
                try:
                    os.remove(source_file)
                except Exception as e:
                    print(f"删除文件失败: {source_file}, {str(e)}")
                # 更新data.json
                voice_data, data_file = load_voice_data()
                if file in voice_data:
                    del voice_data[file]
                    with open(data_file, "w", encoding="utf-8") as f:
                        json.dump(voice_data, f, ensure_ascii=False, indent=2)
        # 递归删除整个目录
        try:
            shutil.rmtree(source_dir)
        except Exception as e:
            print(f"递归删除目录失败: {source_dir}, {str(e)}")
    return True, "分类已删除，相关音频已一并删除"

# 上传音频文件
def upload_audio_file(file, category_id):
    # 验证文件类型（统一转换为小写进行比较）
    original_filename = file.filename
    name, ext = os.path.splitext(original_filename)
    ext = ext.lower()
    # 替换不安全的字符，但保留中文
    safe_filename = ""
    for char in name:
        if char.isalnum() or char in '._- ' or '\u4e00' <= char <= '\u9fff':
            safe_filename += char
        else:
            safe_filename += '_'
    filename = safe_filename + ext
    file_ext = ext
    if file_ext not in ('.wav', '.mp3'):
        return False, "只允许上传WAV或MP3格式的音频文件"
    # 如果分类不存在，使用other
    category_path = os.path.join(VOICE_DIR, category_id)
    if not os.path.exists(category_path):
        category_id = "other"
        category_path = os.path.join(VOICE_DIR, "other")
    # 保存文件
    file_path = os.path.join(category_path, filename)
    file.save(file_path)
    # 更新data.json
    voice_data, data_file = load_voice_data()
    voice_key = f"{category_id}/{filename}"
    voice_url = f"voice/{category_id}/{filename}"
    voice_data[voice_key] = {
        "note": "",
        "path": voice_url,
        "category": category_id
    }
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(voice_data, f, ensure_ascii=False, indent=2)
    return True, "音频文件上传成功"

# 批量上传音频文件
def batch_upload_audio_files(files, category_id):
    success_count = 0
    failed_count = 0
    results = []
    for file in files:
        # 跳过空文件
        if not file.filename:
            continue
        # 处理文件名，保留中文字符，并将扩展名转为小写
        original_filename = file.filename
        name, ext = os.path.splitext(original_filename)
        ext = ext.lower()
        safe_filename = ""
        for char in name:
            if char.isalnum() or char in '._- ' or '\u4e00' <= char <= '\u9fff':
                safe_filename += char
            else:
                safe_filename += '_'
        filename = safe_filename + ext
        file_ext = ext
        # 如果不是支持的格式，尝试转换
        if file_ext not in ['.wav', '.mp3']:
            try:
                temp_uuid = str(uuid.uuid4())
                temp_path = os.path.join(TEMP_DIR, f"{temp_uuid}{file_ext}")
                file.save(temp_path)
                output_filename = os.path.splitext(safe_filename)[0] + ".mp3"
                output_path = os.path.join(TEMP_DIR, f"{temp_uuid}.mp3")
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(temp_path)
                    audio.export(output_path, format="mp3")
                    with open(output_path, 'rb') as f2:
                        file_content = f2.read()
                    try:
                        os.remove(temp_path)
                        os.remove(output_path)
                    except Exception as e:
                        print(f"删除临时文件失败: {str(e)}")
                    from io import BytesIO
                    file = FileStorage(
                        stream=BytesIO(file_content),
                        filename=output_filename,
                        content_type='audio/mpeg'
                    )
                    filename = output_filename
                    file_ext = '.mp3'
                except Exception as e:
                    results.append({
                        "filename": original_filename,
                        "success": False,
                        "message": f"格式转换失败: {str(e)}"
                    })
                    failed_count += 1
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except:
                        pass
                    continue
            except Exception as e:
                results.append({
                    "filename": original_filename,
                    "success": False,
                    "message": f"处理失败: {str(e)}"
                })
                failed_count += 1
                continue
        # 保存文件
        category_path = os.path.join(VOICE_DIR, category_id)
        if not os.path.exists(category_path):
            os.makedirs(category_path)
        file_path = os.path.join(category_path, filename)
        file.save(file_path)
        # 更新data.json
        voice_data, data_file = load_voice_data()
        voice_key = f"{category_id}/{filename}"
        voice_url = f"voice/{category_id}/{filename}"
        voice_data[voice_key] = {
            "note": "",
            "path": voice_url,
            "category": category_id
        }
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(voice_data, f, ensure_ascii=False, indent=2)
        success_count += 1
        results.append({
            "filename": filename,
            "success": True,
            "message": "音频文件上传成功"
        })
    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }

# 删除音频文件
def delete_audio_file(filename):
    # 尝试URL解码文件名，处理可能的编码问题
    try:
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        print(f"删除音频: 原始文件名={filename}, 解码后={decoded_filename}")
    except Exception as e:
        decoded_filename = filename
        print(f"解码文件名失败: {str(e)}")
    
    # 查找文件 - 首先尝试解码后的文件名
    file_path = None
    found_match = False
    
    print(f"开始在 {VOICE_DIR} 中查找文件...")
    
    for root, dirs, files in os.walk(VOICE_DIR):
        print(f"搜索目录: {root}, 包含 {len(files)} 个文件")
        
        # 尝试不同的文件名变体
        for file in files:
            # 尝试原始文件名
            if file.lower() == filename.lower():
                file_path = os.path.join(root, file)
                filename = file  # 使用实际找到的文件名（保留原始大小写）
                found_match = True
                print(f"找到匹配(原始文件名): {file_path}")
                break
            # 尝试解码后的文件名
            if file.lower() == decoded_filename.lower():
                file_path = os.path.join(root, file)
                filename = file  # 使用实际找到的文件名
                found_match = True
                print(f"找到匹配(解码文件名): {file_path}")
                break
        
        if found_match:
            break
    
    if not found_match:
        print(f"未找到匹配的文件: {filename}")
        # 列出所有可能的文件
        all_files = []
        for root, dirs, files in os.walk(VOICE_DIR):
            for file in files:
                all_files.append(os.path.join(root, file))
        print(f"目录中的所有文件: {all_files[:20]}...")  # 只打印前20个避免日志过长
        return False, f"找不到指定的音频文件: {filename}"
    
    # 删除文件
    try:
        os.remove(file_path)
        print(f"成功删除文件: {file_path}")
    except Exception as e:
        print(f"删除文件失败: {str(e)}")
        return False, f"删除文件失败: {str(e)}"
    
    # 更新data.json
    voice_data, data_file = load_voice_data()
    if filename in voice_data:
        del voice_data[filename]
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(voice_data, f, ensure_ascii=False, indent=2)
        print(f"从data.json中移除了记录: {filename}")
    else:
        print(f"警告: {filename} 在data.json中未找到")
    
    return True, "音频文件已删除"

# 确保分类目录存在
def ensure_category_directories():
    categories = load_voice_categories()
    for category in categories["categories"]:
        category_path = os.path.join(VOICE_DIR, category["id"])
        os.makedirs(category_path, exist_ok=True)

# 加载生成历史记录
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# 保存生成历史记录
def save_history(records):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

# 添加生成记录
def add_history_record(model_path, voice_path, text, output_file, generation_time, infer_mode="普通推理", **params):
    records = load_history()
    
    # 获取模型名称
    model_name = model_path.split(os.path.sep)[1] if os.path.sep in model_path else model_path
    
    # 获取参考音频名称
    voice_name = os.path.basename(voice_path)
    
    # 创建记录
    record = {
        "id": str(uuid.uuid4()),
        "model": model_name,
        "voice": voice_name,
        "text": text[:100] + ("..." if len(text) > 100 else ""),  # 截断过长的文本
        "full_text": text,
        "output_file": output_file,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "generation_time": generation_time,  # 生成所需时间（秒）
        "infer_mode": infer_mode,
        "params": params
    }
    
    # 添加到记录列表的开头（最新的记录在前面）
    records.insert(0, record)
    
    # 仅保留最近的100条记录
    if len(records) > 100:
        records = records[:100]
    
    # 保存记录
    save_history(records)
    
    return record

# 加载模型列表
def load_models():
    models = []
    for root, dirs, files in os.walk("model"):
        if "config.yaml" in files:
            model_path = os.path.dirname(os.path.join(root, "config.yaml"))
            model_name = model_path.split(os.path.sep)[1]
            models.append({"name": model_name, "path": model_path})
    return models

# 加载语音数据信息文件
def load_voice_data():
    data_file = os.path.join(VOICE_DIR, "data.json")
    
    # 确保data.json文件存在
    if not os.path.exists(data_file):
        # 如果不存在，创建一个默认的data.json
        create_default_data_json(VOICE_DIR)
    
    # 加载data.json
    with open(data_file, "r", encoding="utf-8") as f:
        try:
            voice_data = json.load(f)
        except json.JSONDecodeError:
            # 如果JSON格式有误，创建一个空字典
            voice_data = {}
    
    return voice_data, data_file

# 加载所有参考音频列表（不按模型区分）
def load_all_voices():
    voices = []
    voice_data, data_file = load_voice_data()
    
    # 确保所有分类目录存在
    ensure_category_directories()
    
    # 扫描语音目录及其子目录下的所有音频文件
    for root, dirs, files in os.walk(VOICE_DIR):
        for file in files:
            if file.endswith((".wav", ".mp3")) and file != "data.json":
                rel_path = os.path.relpath(root, VOICE_DIR)
                category_id = rel_path if rel_path != "." else "other"
                audio_url = f"voice/{category_id}/{file}"
                voice_key = f"{category_id}/{file}"
                if voice_key in voice_data:
                    note = voice_data[voice_key].get("note", "")
                    voice_data[voice_key]["path"] = audio_url
                    voice_data[voice_key]["category"] = category_id
                else:
                    note = ""
                    voice_data[voice_key] = {"note": note, "path": audio_url, "category": category_id}
                voices.append({
                    "name": file,
                    "note": note,
                    "path": audio_url,
                    "category": category_id
                })
    
    # 更新data.json
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(voice_data, f, ensure_ascii=False, indent=2)
    
    return voices

# 创建默认的data.json文件
def create_default_data_json(voice_dir):
    if not os.path.exists(voice_dir):
        os.makedirs(voice_dir)
    
    data_file = os.path.join(voice_dir, "data.json")
    default_data = {}
    
    # 扫描voice目录下的所有音频文件，如果有的话
    if os.path.exists(voice_dir):
        for root, dirs, files in os.walk(voice_dir):
            for file in files:
                if file.endswith((".wav", ".mp3", ".WAV", ".MP3")):
                    rel_path = os.path.relpath(root, voice_dir)
                    category_id = rel_path if rel_path != "." else "other"
                    # 统一扩展名为小写
                    name, ext = os.path.splitext(file)
                    ext = ext.lower()
                    filename = name + ext
                    # 相对于static的路径
                    full_path = os.path.join(root, file)
                    rel_static_path = os.path.relpath(full_path, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
                    voice_key = f"{category_id}/{filename}"
                    default_data[voice_key] = {
                        "note": "",
                        "path": rel_static_path,
                        "category": category_id
                    }
    
    # 写入默认data.json
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(default_data, f, ensure_ascii=False, indent=2)

# 更新参考音频备注
def update_voice_note(voice_name, note):
    voice_data, data_file = load_voice_data()
    
    # 更新备注
    if voice_name in voice_data:
        voice_data[voice_name]["note"] = note
    else:
        # 查找音频文件的实际路径
        for root, dirs, files in os.walk(VOICE_DIR):
            if voice_name in files:
                full_path = os.path.join(root, voice_name)
                rel_static_path = os.path.relpath(full_path, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
                
                rel_path = os.path.relpath(root, VOICE_DIR)
                category_id = rel_path if rel_path != "." else "other"
                
                voice_key = f"{category_id}/{voice_name}"
                voice_data[voice_key] = {
                    "note": note,
                    "path": rel_static_path,
                    "category": category_id
                }
                break
    
    # 写入更新后的data.json
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(voice_data, f, ensure_ascii=False, indent=2)

# 读取配置文件
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

# 保存配置文件
def save_config(config_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=4)

# 保存剪映项目目录
def save_jianying_project_dir(project_dir):
    config = load_config()
    config["jianying_project_dir"] = project_dir
    save_config(config)

# 保存DeepSeek API Key
def save_deepseek_api_key(api_key):
    config = load_config()
    config["deepseek_api_key"] = api_key
    save_config(config)

# 读取DeepSeek API Key
def get_deepseek_api_key():
    config = load_config()
    return config.get("deepseek_api_key", "")

@app.route('/')
def index():
    models = load_models()
    # 默认选择第一个模型
    default_model = models[0]["path"] if models else ""
    # 加载语音文件
    voices = load_all_voices()
    # 加载语音分类
    categories = load_voice_categories()
    # 加载生成历史记录
    history = load_history()
    # 加载配置信息
    config = load_config()
    jianying_project_dir = config.get("jianying_project_dir", "")
    deepseek_api_key = config.get("deepseek_api_key", "")
    
    return render_template('index.html', 
                          models=models, 
                          voices=voices,
                          voice_categories=categories["categories"],
                          selected_model=default_model, 
                          history=history,
                          jianying_project_dir=jianying_project_dir,
                          deepseek_api_key=deepseek_api_key)

@app.route('/get_voices', methods=['GET'])
def get_voices():
    voices = load_all_voices()
    categories = load_voice_categories()
    return jsonify({
        "voices": voices,
        "categories": categories["categories"]
    })

@app.route('/update_voice_category', methods=['POST'])
def update_voice_category_route():
    voice_name = request.form.get('voice_name')
    category_id = request.form.get('category_id')
    
    if not voice_name or not category_id:
        return jsonify({"error": "缺少必要参数"}), 400
    
    # 更新音频分类
    success = update_voice_category(voice_name, category_id)
    
    # 移动文件到对应分类目录
    if success:
        # 查找音频文件
        for root, dirs, files in os.walk(VOICE_DIR):
            if voice_name in files:
                source_path = os.path.join(root, voice_name)
                dest_path = os.path.join(VOICE_DIR, category_id, voice_name)
                
                # 确保目标目录存在
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                # 如果目标文件已存在，先删除
                if os.path.exists(dest_path) and source_path != dest_path:
                    os.remove(dest_path)
                
                # 移动文件（如果源文件与目标文件不同）
                if source_path != dest_path:
                    shutil.move(source_path, dest_path)
                break
    
    return jsonify({"success": success})

@app.route('/generate', methods=['POST'])
def generate():
    try:
        model_dir = request.form.get('model')
        voice_path = request.form.get('voice')
        text = request.form.get('text')
        infer_mode = request.form.get('infer_mode', '普通推理')
        
        if not all([model_dir, voice_path, text]):
            return jsonify({"error": "缺少必要参数"}), 400
        
        # 获取生成参数
        generation_params = {
            'do_sample': request.form.get('do_sample', 'true').lower() == 'true',
            'top_p': float(request.form.get('top_p', 0.8)),
            'top_k': int(request.form.get('top_k', 30)),
            'temperature': float(request.form.get('temperature', 1.0)),
            'length_penalty': float(request.form.get('length_penalty', 0.0)),
            'num_beams': int(request.form.get('num_beams', 3)),
            'repetition_penalty': float(request.form.get('repetition_penalty', 10.0)),
            'max_mel_tokens': int(request.form.get('max_mel_tokens', 600)),
            'max_text_tokens_per_sentence': int(request.form.get('max_text_tokens_per_sentence', 120))
        }
        
        # 记录开始时间
        start_time = time.time()
        
        # 将voice_path转换为绝对路径
        if not os.path.isabs(voice_path):
            # 如果是相对路径，拼接成绝对路径
            if voice_path.startswith('voice/'):
                voice_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', voice_path)
            else:
                voice_path = os.path.abspath(voice_path)
        
        # 初始化TTS模型
        tts = IndexTTS(model_dir=model_dir, cfg_path=f"{model_dir}/config.yaml")
        
        # 生成唯一文件名
        output_filename = f"output_{uuid.uuid4().hex[:8]}.wav"
        output_path = os.path.join("static", "output", output_filename)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 生成语音
        if infer_mode == "批次推理":
            sentences_bucket_max_size = int(request.form.get('sentences_bucket_max_size', 4))
            tts.infer_fast(
                voice_path, 
                text, 
                output_path,
                sentences_bucket_max_size=sentences_bucket_max_size,
                **generation_params
            )
        else:
            tts.infer(
                voice_path, 
                text, 
                output_path,
                **generation_params
            )
        
        # 计算生成时间
        end_time = time.time()
        generation_time = round(end_time - start_time, 2)  # 四舍五入到2位小数
        
        # 添加生成记录
        record = add_history_record(
            model_dir, 
            voice_path, 
            text, 
            output_path, 
            generation_time,
            infer_mode=infer_mode,
            **generation_params
        )
        
        return jsonify({
            "success": True,
            "output_file": output_path,
            "message": "语音生成成功!",
            "record": record,
            "generation_time": generation_time
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update-note', methods=['POST'])
def update_note():
    voice_name = request.form.get('voice_name')
    note = request.form.get('note')
    
    if not voice_name:
        return jsonify({"error": "请指定音频名称"}), 400
    
    update_voice_note(voice_name, note)
    return jsonify({"success": True})

@app.route('/audio/<path:filename>')
def get_audio(filename):
    # 检查路径是否已经包含static前缀
    if filename.startswith('static/'):
        return send_file(filename)
    else:
        # 如果不是从static目录开始的路径，确保添加static前缀
        # 将音频文件路径映射到static目录下
        if filename.startswith('voice/'):
            # 如果是voice路径，确保添加static前缀
            full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', filename)
        else:
            # 其他情况尝试从根目录加载
            full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        
        # 添加错误处理和调试信息
        if not os.path.exists(full_path):
            app.logger.error(f"File not found: {full_path}")
            return jsonify({"error": f"文件未找到: {full_path}"}), 404
        
        return send_file(full_path)

@app.route('/get_history', methods=['GET'])
def get_history():
    history = load_history()
    return jsonify(history)

@app.route('/delete_record', methods=['POST'])
def delete_record():
    record_id = request.form.get('record_id')
    if not record_id:
        return jsonify({"error": "未指定记录ID"}), 400
    
    records = load_history()
    # 过滤掉要删除的记录
    records = [r for r in records if r.get('id') != record_id]
    save_history(records)
    
    return jsonify({"success": True})

# 检查剪映项目目录
def check_jianying_project_dir(project_dir):
    # 验证是否为剪映项目目录
    if not os.path.isdir(project_dir):
        return False, "指定的路径不是有效目录"
    
    # 检查是否包含项目文件夹（排除.recycle_bin和root_meta_info.json）
    valid_dirs = [d for d in os.listdir(project_dir) 
                  if os.path.isdir(os.path.join(project_dir, d)) and d != '.recycle_bin']
    
    if not valid_dirs:
        return False, "未找到有效的剪映项目"
    
    # 保存有效的剪映项目目录到配置文件
    save_jianying_project_dir(project_dir)
    
    return True, valid_dirs


def add_audio_to_subtitles(project_dir, project_name):
    try:
        project_path = os.path.join(project_dir, project_name)
        draft_content_path = os.path.join(project_path, "draft_content.json")

        with open(draft_content_path, "r", encoding="utf-8") as f:
            draft_content = json.load(f)

        # 备份原始文件
        backup_path = f"{draft_content_path}.bak"
        shutil.copy(draft_content_path, backup_path)

        # 获取材料库
        materials = draft_content.get("materials", {})
        texts = materials.get("texts", [])
        audios = materials.get("audios", [])
        animations = materials.get("material_animations", [])

        # 获取轨道
        tracks = draft_content.get("tracks", [])

        # 查找文本轨道和音频轨道
        text_track = None
        audio_track = None
        for track in tracks:
            if track.get("type") == "text":
                text_track = track
            elif track.get("type") == "audio":
                audio_track = track

        # 如果没有文本轨道，创建一个
        if text_track is None:
            text_track = {
                "attribute": 0,
                "flag": 0,
                "id": str(uuid.uuid4()).upper(),
                "is_default_name": True,
                "name": "",
                "segments": [],
                "type": "text"
            }
            tracks.append(text_track)

        # 如果没有音频轨道，创建一个
        if audio_track is None:
            audio_track = {
                "attribute": 0,
                "flag": 0,
                "id": str(uuid.uuid4()).upper(),
                "is_default_name": True,
                "name": "",
                "segments": [],
                "type": "audio"
            }
            tracks.append(audio_track)

        # 用于记录添加的音频数量
        added_audio_count = 0

        # 创建文本ID到文本对象的映射
        text_id_map = {text["id"]: text for text in texts}

        # 创建音频ID到音频对象的映射
        audio_id_map = {audio["id"]: audio for audio in audios}

        # 创建文本ID到已关联音频的映射
        text_has_audio = {}
        for audio in audios:
            text_id = audio.get("text_id")
            if text_id:
                text_has_audio[text_id] = True

        # 遍历所有字幕
        for text in texts:
            text_id = text.get("id")

            # 如果该字幕已经有关联的音频，跳过
            if text_has_audio.get(text_id):
                continue

            # 为这个字幕创建一个新的音频ID
            audio_id = str(uuid.uuid4()).upper()

            # 尝试获取字幕内容
            text_content = ""
            try:
                content_json = text.get("content", "{}")
                content_data = json.loads(content_json)
                text_content = content_data.get("text", "")
            except:
                text_content = content_json

            # 创建音频材料
            audio_path_dir = os.path.join(project_path, 'textReading')
            audio_path = f"{audio_path_dir}/{audio_id.lower()}.wav"

            # 默认时长（微秒），先设置为0
            duration = 0

            audio_item = {
                "app_id": 0,
                "check_flag": 1,
                "duration": duration,
                "id": audio_id,
                "name": text_content[:20] + ("..." if len(text_content) > 20 else ""),
                "path": audio_path,
                "text_id": text_id,  # 关键：通过text_id关联
                "type": "text_to_audio"
            }
            audios.append(audio_item)
            audio_id_map[audio_id] = audio_item
            text_has_audio[text_id] = True

            # 创建动画ID（占位）
            animation_id = str(uuid.uuid4()).upper()
            animation_item = {
                "animations": [],
                "id": animation_id,
                "multi_language_current": "none",
                "type": "sticker_animation"
            }
            animations.append(animation_item)

            # 获取该字幕在文本轨道中的segment
            text_segment = None
            for segment in text_track.get("segments", []):
                if segment.get("material_id") == text_id:
                    text_segment = segment
                    break

            # 如果没有找到文本片段，创建一个新的
            if text_segment is None:
                # 创建新的文本轨道片段
                text_segment = {
                    "caption_info": None,
                    "cartoon": False,
                    "clip": {
                        "alpha": 1.0,
                        "flip": {"horizontal": False, "vertical": False},
                        "rotation": 0.0,
                        "scale": {"x": 1.0, "y": 1.0},
                        "transform": {"x": 0.0, "y": -0.7721662468513853}
                    },
                    "common_keyframes": [],
                    "enable_adjust": False,
                    "extra_material_refs": [animation_id],
                    "group_id": "",
                    "id": str(uuid.uuid4()).upper(),
                    "material_id": text_id,
                    "render_index": 14000 + len(text_track["segments"]),
                    "target_timerange": {
                        "duration": 3000000,  # 默认3秒
                        "start": 0
                    },
                    "track_attribute": 0,
                    "track_render_index": 1,
                    "uniform_scale": {"on": True, "value": 1.0},
                    "visible": True,
                    "volume": 1.0
                }
                text_track["segments"].append(text_segment)

            # 获取字幕的开始时间和时长
            start_time = text_segment.get("target_timerange", {}).get("start", 0)
            duration = text_segment.get("target_timerange", {}).get("duration", 3000000)

            # 创建音频轨道segment
            audio_segment = {
                "caption_info": None,
                "cartoon": False,
                "clip": None,
                "common_keyframes": [],
                "enable_adjust": False,
                "group_id": "",
                "id": str(uuid.uuid4()).upper(),
                "material_id": audio_id,
                "render_index": 0,
                "source_timerange": {
                    "duration": duration,
                    "start": 0
                },
                "target_timerange": {
                    "duration": duration,
                    "start": start_time
                },
                "track_attribute": 0,
                "track_render_index": 0,
                "visible": True,
                "volume": 1
            }
            audio_track["segments"].append(audio_segment)

            # 更新文本轨道的segment，添加extra_material_refs（动画）
            if "extra_material_refs" in text_segment:
                text_segment["extra_material_refs"].append(animation_id)
            else:
                text_segment["extra_material_refs"] = [animation_id]

            added_audio_count += 1

        # 更新材料库和轨道
        materials['audios'] = audios
        materials['material_animations'] = animations
        draft_content['materials'] = materials
        draft_content['tracks'] = tracks

        # 保存更新后的项目文件
        with open(draft_content_path, "w", encoding="utf-8") as f:
            json.dump(draft_content, f, ensure_ascii=False, indent=4)

        return True, f"成功为{added_audio_count}个字幕添加了音频信息"
    except Exception as e:
        return False, f"添加音频失败: {str(e)}"


# 在load_jianying_audio_info中调用
def load_jianying_audio_info(project_dir, project_name, get_all_subtitles=False):
    if get_all_subtitles:
        # 调用修复后的函数
        success, result = add_audio_to_subtitles(project_dir, project_name)
        if not success:
            return False, result

    # 其余代码保持不变...
# 加载剪映项目中的音频信息
def load_jianying_audio_info(project_dir, project_name, get_all_subtitles=False):
    if get_all_subtitles:
        add_audio_to_subtitles(project_dir, project_name)
    project_path = os.path.join(project_dir, project_name)
    draft_content_path = os.path.join(project_path, "draft_content.json")
    
    if not os.path.exists(draft_content_path):
        return False, "未找到draft_content.json文件"
    
    try:
        with open(draft_content_path, "r", encoding="utf-8") as f:
            draft_content = json.load(f)
        
        # 提取音频信息
        audio_infos = []
        materials_audios = draft_content.get("materials", {}).get("audios", [])
        materials_texts = draft_content.get("materials", {}).get("texts", [])
        
        # 创建文本ID到文本内容的映射
        text_map = {}
        for text in materials_texts:
            text_id = text.get("id", "")
            content_json = text.get("content", "")
            
            try:
                # 解析内容JSON以提取文本
                content_data = json.loads(content_json)
                text_content = content_data.get('text', '')
                text_map[text_id] = text_content
            except:
                text_map[text_id] = ""
        
        # 提取音频信息
        for audio in materials_audios:
            if audio.get("type") == "text_to_audio":
                audio_id = audio.get("id", "")
                audio_name = audio.get("name", "未命名")
                audio_path = audio.get("path", "")
                text_id = audio.get("text_id", "")
                
                # 替换路径中的占位符
                actual_path = audio_path
                if "##_draftpath_placeholder_" in audio_path and "_##" in audio_path:
                    placeholder_part = audio_path.split("##_draftpath_placeholder_")[1].split("_##")[0]
                    actual_path = audio_path.replace(f"##_draftpath_placeholder_{placeholder_part}_##", project_path)
                
                # 检查音频文件是否存在
                file_exists = os.path.exists(actual_path)
                
                # 如果在原路径找不到，尝试在textReading目录中查找
                if not file_exists and ("textReading/" in audio_path or "textReading\\" in audio_path):
                    # 提取文件名
                    if "\\" in audio_path:
                        file_name = audio_path.split("textReading\\")[-1]
                    else:
                        file_name = audio_path.split("textReading/")[-1]
                    
                    # 尝试在textReading目录中查找
                    text_reading_path = os.path.join(project_path, "textReading", file_name)
                    if os.path.exists(text_reading_path):
                        actual_path = text_reading_path
                        file_exists = True
                
                # 获取关联的文本内容
                text_content = text_map.get(text_id, "")
                
                # 检查是否存在替换状态标记
                status = audio.get("status", False)
                
                audio_infos.append({
                    "id": audio_id,
                    "name": audio_name,
                    "path": actual_path,
                    "file_exists": file_exists,
                    "text_id": text_id,
                    "text_content": text_content,
                    "status": status
                })
        
        return True, audio_infos
    except Exception as e:
        return False, f"解析项目文件失败: {str(e)}"

# 替换剪映项目中的音频
def replace_jianying_audio(project_dir, project_name, audio_replacements, sync_position=False, append_to_last=False):
    """
    替换剪映项目中的多个音频
    
    :param project_dir: 剪映项目目录
    :param project_name: 项目名称
    :param audio_replacements: 音频替换数据列表，每项包含 audio_id、new_audio_path、duration
    :param sync_position: 是否同步字幕和音频的开始位置
    :param append_to_last: 是否紧跟在上一段字幕和音频后面
    :return: (成功标志, 消息)
    """
    project_path = os.path.join(project_dir, project_name)
    draft_content_path = os.path.join(project_path, "draft_content.json")
    
    try:
        # 读取项目文件
        with open(draft_content_path, "r", encoding="utf-8") as f:
            draft_content = json.load(f)
        
        # 备份原始文件
        backup_path = f"{draft_content_path}.bak"
        shutil.copy(draft_content_path, backup_path)
        
        # 替换音频文件
        materials_audios = draft_content.get("materials", {}).get("audios", [])
        materials_texts = draft_content.get("materials", {}).get("texts", [])
        tracks = draft_content.get("tracks", [])
        replaced_count = 0
        
        # 创建音频ID到替换路径和时长的映射
        replacement_map = {item['audio_id']: {
            'path': os.path.abspath(item['new_audio_path']), 
            'duration': item['duration']
        } for item in audio_replacements}
        
        # 创建音频ID到文本ID的映射，用于查找关联关系
        audio_to_text_map = {}
        for audio in materials_audios:
            audio_id = audio.get("id")
            text_id = audio.get("text_id")
            if audio_id and text_id:
                audio_to_text_map[audio_id] = text_id
        
        # 创建文本ID到音频ID列表的映射
        text_to_audio_map = {}
        for text in materials_texts:
            text_id = text.get("id")
            audio_ids = text.get("text_to_audio_ids", [])
            if text_id and audio_ids:
                text_to_audio_map[text_id] = audio_ids
        
        # 确保textReading目录存在
        text_reading_dir = os.path.join(project_path, "textReading")
        os.makedirs(text_reading_dir, exist_ok=True)
        
        # 第1步：替换材料库中的音频文件并更新时长
        for audio in materials_audios:
            audio_id = audio.get("id")
            if audio_id in replacement_map:
                replacement_info = replacement_map[audio_id]
                
                # 更新音频时长
                audio["duration"] = replacement_info['duration']
                
                # 从path中提取文件名
                original_path = audio.get("path", "")
                if "textReading/" in original_path or "textReading\\" in original_path:
                    # 如果路径中包含textReading，提取文件名
                    if "\\" in original_path:
                        file_name = original_path.split("textReading\\")[-1]
                    else:
                        file_name = original_path.split("textReading/")[-1]
                else:
                    # 使用一个默认的文件名
                    file_name = f"{audio_id.lower()}.wav"
                
                # 替换路径中的占位符，获取实际物理路径
                actual_path = original_path
                if "##_draftpath_placeholder_" in original_path and "_##" in original_path:
                    placeholder_part = original_path.split("##_draftpath_placeholder_")[1].split("_##")[0]
                    actual_path = original_path.replace(f"##_draftpath_placeholder_{placeholder_part}_##", project_path)
                
                # 确保目标目录存在
                target_dir = os.path.dirname(actual_path)
                os.makedirs(target_dir, exist_ok=True)
                
                # 替换实际物理文件
                shutil.copy(replacement_info['path'], actual_path)
                
                # 如果actual_path不在textReading目录下，也复制到textReading目录
                if "textReading" not in actual_path:
                    text_reading_file_path = os.path.join(text_reading_dir, file_name)
                    shutil.copy(replacement_info['path'], text_reading_file_path)
                    
                    # 更新音频文件路径
                    if "##_draftpath_placeholder_" in original_path:
                        # 保持原来的占位符格式
                        new_path = f"##_draftpath_placeholder_{placeholder_part}_##/textReading/{file_name}"
                        audio["path"] = new_path
                
                # 标记音频已被替换
                audio["status"] = True
                
                print(f"已替换音频: {audio_id}, 路径: {actual_path}, 新时长: {replacement_info['duration']}")
                replaced_count += 1
        
        # 第2步：更新轨道中的音频时长信息
        for track in tracks:
            if track.get("type") == "audio":
                for segment in track.get("segments", []):
                    segment_id = segment.get("id")
                    material_id = segment.get("material_id")
                    
                    # 查找与该segment关联的音频
                    for audio_id, info in replacement_map.items():
                        # 场景1：直接匹配segment的ID
                        if segment_id == audio_id:
                            # 更新源时长和目标时长
                            if "source_timerange" in segment:
                                segment["source_timerange"]["duration"] = info['duration']
                            if "target_timerange" in segment:
                                segment["target_timerange"]["duration"] = info['duration']
                            print(f"更新轨道音频时长 (直接匹配): {segment_id}, 新时长: {info['duration']}")
                        
                        # 场景2：通过material_id匹配
                        elif material_id == audio_id:
                            # 更新源时长和目标时长
                            if "source_timerange" in segment:
                                segment["source_timerange"]["duration"] = info['duration']
                            if "target_timerange" in segment:
                                segment["target_timerange"]["duration"] = info['duration']
                            print(f"更新轨道音频时长 (通过材料ID): {material_id}, 新时长: {info['duration']}")
                        
                        # 场景3：通过text_to_audio_ids关联匹配
                        else:
                            # 查找该音频关联的文本
                            text_id = audio_to_text_map.get(audio_id)
                            if text_id:
                                # 查找该文本关联的所有音频ID
                                related_audio_ids = text_to_audio_map.get(text_id, [])
                                # 如果当前segment的ID在关联的音频ID中
                                if segment_id in related_audio_ids:
                                    # 更新源时长和目标时长
                                    if "source_timerange" in segment:
                                        segment["source_timerange"]["duration"] = info['duration']
                                    if "target_timerange" in segment:
                                        segment["target_timerange"]["duration"] = info['duration']
                                    print(f"更新轨道音频时长 (通过关联): {segment_id}, 关联文本: {text_id}, 新时长: {info['duration']}")
        
        # 第3步：更新字幕轨道的显示时长和位置（如果启用了相关选项）
        
        # 如果选择了连续排列，先找出要处理的音频段落的信息
        first_segment_start = None
        audio_segments_to_process = []
        
        if append_to_last:
            # 收集所有需要处理的音频段落，按ID顺序匹配
            for audio_id, info in replacement_map.items():
                # 查找对应的音频段落
                for track in [t for t in tracks if t.get("type") == "audio"]:
                    for segment in track.get("segments", []):
                        if segment.get("material_id") == audio_id:
                            audio_segments_to_process.append({
                                'segment': segment,
                                'audio_id': audio_id,
                                'text_id': audio_to_text_map.get(audio_id),
                                'duration': info['duration']
                            })
                            # 记录第一个段落的原始开始位置
                            if first_segment_start is None and "target_timerange" in segment:
                                first_segment_start = segment["target_timerange"].get("start", 0)
                            break
            
            # 按原始开始位置排序
            if audio_segments_to_process:
                audio_segments_to_process.sort(key=lambda x: x['segment'].get("target_timerange", {}).get("start", 0))
                # 以第一个段落的开始位置作为基准
                first_segment_start = audio_segments_to_process[0]['segment'].get("target_timerange", {}).get("start", 0)
                print(f"找到第一个段落的开始位置: {first_segment_start}")
        
        # 处理每个轨道中的字幕段落
        for track in tracks:
            if track.get("type") == "text":
                for segment in track.get("segments", []):
                    material_id = segment.get("material_id")
                    segment_timerange = segment.get("target_timerange", {})
                    
                    # 查找是否有与此字幕关联的音频被替换
                    for audio_id, info in replacement_map.items():
                        text_id = audio_to_text_map.get(audio_id)
                        # 如果字幕的material_id与音频关联的文本ID匹配
                        if material_id == text_id:
                            # 找到对应的音频轨道段落，获取其开始位置
                            audio_segment_start = None
                            audio_segment = None
                            
                            # 查找对应的音频段落
                            for audio_track in [t for t in tracks if t.get("type") == "audio"]:
                                for a_segment in audio_track.get("segments", []):
                                    if a_segment.get("material_id") == audio_id:
                                        audio_segment = a_segment
                                        audio_segment_start = a_segment.get("target_timerange", {}).get("start", None)
                                        break
                                if audio_segment is not None:
                                    break
                            
                            # 更新字幕的显示时长与音频时长一致
                            if "target_timerange" in segment:
                                segment["target_timerange"]["duration"] = info['duration']
                                print(f"更新字幕显示时长: 字幕ID {material_id}, 关联音频 {audio_id}, 新时长: {info['duration']}")
                            
                            # 不在这里处理连续排列的情况，因为我们已经收集了所有需要处理的音频段落
                            
                            # 如果启用了同步选项，保持字幕位置不变，调整音频位置
                            if sync_position and audio_segment is not None and not append_to_last:
                                # 获取字幕的开始位置
                                subtitle_start = segment.get("target_timerange", {}).get("start", None)
                                if subtitle_start is not None:
                                    # 将音频的开始位置调整为与字幕一致
                                    audio_segment["target_timerange"]["start"] = subtitle_start
                                    print(f"调整音频位置与字幕一致: 字幕ID {material_id}, 音频ID {audio_id}, 位置: {subtitle_start}")
        
        # 处理连续排列的情况
        if append_to_last and audio_segments_to_process and first_segment_start is not None:
            print("执行连续排列...")
            current_position = first_segment_start
            
            # 按顺序处理所有音频段落
            for i, item in enumerate(audio_segments_to_process):
                audio_id = item['audio_id']
                text_id = item['text_id']
                duration = item['duration']
                audio_segment = item['segment']
                
                # 更新音频段落的位置
                if "target_timerange" in audio_segment:
                    audio_segment["target_timerange"]["start"] = current_position
                    print(f"调整音频位置: 音频ID {audio_id}, 新位置: {current_position}")
                
                # 更新对应的字幕段落的位置
                for track in [t for t in tracks if t.get("type") == "text"]:
                    for text_segment in track.get("segments", []):
                        if text_segment.get("material_id") == text_id and "target_timerange" in text_segment:
                            text_segment["target_timerange"]["start"] = current_position
                            print(f"调整字幕位置: 字幕ID {text_id}, 新位置: {current_position}")
                            break
                
                # 更新下一个位置
                current_position += duration
        
        # 保存更新后的项目文件
        with open(draft_content_path, "w", encoding="utf-8") as f:
            json.dump(draft_content, f, ensure_ascii=False)
        
        return True, f"成功替换了{replaced_count}个音频"
    except Exception as e:
        print(f"替换音频失败: {str(e)}")
        return False, f"替换音频失败: {str(e)}"

@app.route('/check_jianying_project', methods=['POST'])
def check_jianying_project():
    project_dir = request.form.get('project_dir')
    if not project_dir:
        return jsonify({"error": "未指定项目目录"}), 400
    
    success, result = check_jianying_project_dir(project_dir)
    if success:
        return jsonify({
            "success": True,
            "projects": result
        })
    else:
        return jsonify({"error": result}), 400

@app.route('/load_jianying_audio', methods=['POST'])
def load_jianying_audio():
    project_dir = request.form.get('project_dir')
    project_name = request.form.get('project_name')
    get_all_subtitles = request.form.get('get_all_subtitles', 'false').lower() == 'true'
    
    if not project_dir or not project_name:
        return jsonify({"error": "缺少必要参数"}), 400
    
    success, result = load_jianying_audio_info(project_dir, project_name, get_all_subtitles)
    if success:
        return jsonify({
            "success": True,
            "audio_infos": result
        })
    else:
        return jsonify({"error": result}), 400

@app.route('/replace_jianying_audio', methods=['POST'])
def replace_jianying_audio_route():
    try:
        project_dir = request.form.get('project_dir')
        project_name = request.form.get('project_name')
        audio_data = request.form.get('audio_data')  # 包含音频ID和文本的JSON数据
        model_dir = request.form.get('model')
        voice_path = request.form.get('voice')
        sync_position = request.form.get('sync_position', 'false').lower() == 'true'
        append_to_last = request.form.get('append_to_last', 'false').lower() == 'true'
        
        if not all([project_dir, project_name, audio_data, model_dir, voice_path]):
            return jsonify({"error": "缺少必要参数"}), 400
        
        # 解析音频数据
        try:
            audio_items = json.loads(audio_data)
        except:
            return jsonify({"error": "解析音频数据失败"}), 400
        
        if not audio_items:
            return jsonify({"error": "没有选择要替换的音频"}), 400
        
        # 记录开始时间
        start_time = time.time()
        
        # 将voice_path转换为绝对路径
        if not os.path.isabs(voice_path):
            # 如果是相对路径，拼接成绝对路径
            if voice_path.startswith('voice/'):
                voice_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', voice_path)
            else:
                voice_path = os.path.abspath(voice_path)
        
        # 检查文件是否存在
        if not os.path.exists(voice_path):
            return jsonify({"error": f"音频文件不存在: {voice_path}"}), 400
        
        # 初始化TTS模型
        tts = IndexTTS(model_dir=model_dir, cfg_path=f"{model_dir}/config.yaml")
        
        # 为每个音频生成语音并替换
        results = []
        success_count = 0
        failed_count = 0
        audio_replacements = []
        
        for item in audio_items:
            audio_id = item.get('id')
            text = item.get('text')
            
            if not audio_id or not text:
                results.append({
                    "id": audio_id,
                    "success": False,
                    "message": "缺少音频ID或文本内容"
                })
                failed_count += 1
                continue
            
            try:
                # 生成唯一文件名
                output_filename = f"output_{uuid.uuid4().hex[:8]}.wav"
                output_path = os.path.join("static", "output", output_filename)
                
                # 确保输出目录存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 生成语音
                tts.infer(voice_path, text, output_path)
                
                # 获取音频时长（微秒）
                from pydub import AudioSegment
                audio = AudioSegment.from_file(output_path)
                duration_us = int(audio.duration_seconds * 1000000)  # 转换为微秒
                
                # 转换为绝对路径
                abs_output_path = os.path.abspath(output_path)
                
                # 添加到替换列表
                audio_replacements.append({
                    'audio_id': audio_id,
                    'new_audio_path': abs_output_path,
                    'duration': duration_us
                })
                
                results.append({
                    "id": audio_id,
                    "success": True,
                    "output_file": output_path,  # 这里保持相对路径用于前端显示
                    "duration": duration_us
                })
                success_count += 1
            except Exception as e:
                results.append({
                    "id": audio_id,
                    "success": False,
                    "message": str(e)
                })
                failed_count += 1
        
        # 替换剪映项目中的音频
        if audio_replacements:
            success, message = replace_jianying_audio(project_dir, project_name, audio_replacements, sync_position, append_to_last)
            if not success:
                return jsonify({"error": message}), 500
        
        # 计算生成时间
        end_time = time.time()
        generation_time = round(end_time - start_time, 2)
        
        return jsonify({
            "success": True,
            "message": f"批量处理完成，成功: {success_count}，失败: {failed_count}",
            "results": results,
            "generation_time": generation_time
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 保存剪映项目中的文本内容
def save_jianying_text(project_dir, project_name, text_id, audio_id, text_content):
    """
    保存剪映项目中文本的内容
    
    :param project_dir: 剪映项目目录
    :param project_name: 项目名称
    :param text_id: 文本ID
    :param audio_id: 关联的音频ID
    :param text_content: 新的文本内容
    :return: (成功标志, 消息)
    """
    project_path = os.path.join(project_dir, project_name)
    draft_content_path = os.path.join(project_path, "draft_content.json")
    
    try:
        # 读取项目文件
        with open(draft_content_path, "r", encoding="utf-8") as f:
            draft_content = json.load(f)
        
        # 备份原始文件
        backup_path = f"{draft_content_path}.textbak"
        shutil.copy(draft_content_path, backup_path)
        
        # 查找并更新文本内容
        materials_texts = draft_content.get("materials", {}).get("texts", [])
        updated = False
        
        for text in materials_texts:
            if text.get("id") == text_id:
                # 更新文本内容
                content_data = json.loads(text.get("content", "{}"))
                content_data["text"] = text_content
                # 如果有styles数据，更新文本长度
                if "styles" in content_data:
                    for style in content_data["styles"]:
                        if "range" in style and len(style["range"]) >= 2:
                            style["range"][1] = len(text_content)
                
                # 更新回文本对象
                text["content"] = json.dumps(content_data)
                updated = True
                print(f"已更新文本: {text_id}, 新内容: {text_content}")
                break
        
        if not updated:
            return False, f"未找到指定ID的文本: {text_id}"
        
        # 保存更新后的项目文件
        with open(draft_content_path, "w", encoding="utf-8") as f:
            json.dump(draft_content, f, ensure_ascii=False)
        
        return True, "文本内容已成功保存"
    except Exception as e:
        print(f"保存文本失败: {str(e)}")
        return False, f"保存文本失败: {str(e)}"

@app.route('/save_jianying_text', methods=['POST'])
def save_jianying_text_route():
    try:
        project_dir = request.form.get('project_dir')
        project_name = request.form.get('project_name')
        text_id = request.form.get('text_id')
        audio_id = request.form.get('audio_id')
        text_content = request.form.get('text_content')
        
        if not all([project_dir, project_name, text_id, text_content]):
            return jsonify({"error": "缺少必要参数"}), 400
        
        success, message = save_jianying_text(project_dir, project_name, text_id, audio_id, text_content)
        
        if success:
            return jsonify({
                "success": True,
                "message": message
            })
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def load_available_fonts():
    """加载可用字体列表"""
    fonts = []
    for font_file in os.listdir(FONT_DIR):
        if font_file.endswith(('.ttf', '.otf')):
            font_path = os.path.join(FONT_DIR, font_file)
            font_name = os.path.splitext(font_file)[0]
            fonts.append({
                'name': font_name,
                'path': font_path
            })
    return fonts

@app.route('/get_available_fonts', methods=['GET'])
def get_available_fonts():
    """获取可用字体列表"""
    try:
        fonts = load_available_fonts()
        return jsonify({
            'success': True,
            'fonts': fonts
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/export_jianying_subtitles', methods=['POST'])
def export_jianying_subtitles():
    """导出剪映项目字幕为TXT的路由"""
    try:
        project_dir = request.form.get('project_dir')
        project_name = request.form.get('project_name')
        
        if not project_dir or not project_name:
            return jsonify({
                'success': False,
                'error': '请提供项目目录和工程名称'
            })
            
        texts, error = load_jianying_text_info(project_dir, project_name)
        if error:
            return jsonify({
                'success': False,
                'error': error
            })
        
        # 提取每个字幕的文本内容并拼接
        subtitles_text = ""
        for text_info in texts:
            content = text_info.get('content', '')
            try:
                # 尝试解析JSON提取文本
                content_data = json.loads(content)
                text_content = content_data.get('text', '')
                if text_content:
                    subtitles_text += text_content + "\n\n"
            except:
                # 如果解析失败，直接使用内容
                if content:
                    subtitles_text += content + "\n\n"
        
        return jsonify({
            'success': True,
            'subtitles_text': subtitles_text
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def load_jianying_text_info(project_dir, project_name):
    """加载剪映项目中的文本信息"""
    try:
        draft_file = os.path.join(project_dir, project_name, 'draft_content.json')
        if not os.path.exists(draft_file):
            return None, "找不到工程文件"
            
        with open(draft_file, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
            
        texts = []
        for text in draft_data.get('materials', {}).get('texts', []):
            text_info = {
                'id': text.get('id'),
                'content': text.get('content', ''),
                'current_font': text.get('font_path', ''),
                'font_size': text.get('font_size', 15),
                'text_color': text.get('text_color', '#FFFFFF')
            }
            texts.append(text_info)
            
        return texts, None
    except Exception as e:
        return None, str(e)

@app.route('/load_jianying_text', methods=['POST'])
def load_jianying_text_route():
    """加载剪映项目文本信息的路由"""
    try:
        project_dir = request.form.get('project_dir')
        project_name = request.form.get('project_name')
        
        if not project_dir or not project_name:
            return jsonify({
                'success': False,
                'error': '请提供项目目录和工程名称'
            })
            
        texts, error = load_jianying_text_info(project_dir, project_name)
        if error:
            return jsonify({
                'success': False,
                'error': error
            })
            
        return jsonify({
            'success': True,
            'texts': texts
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def replace_jianying_font(project_dir, project_name, text_replacements):
    """替换剪映项目中的字体"""
    try:
        draft_file = os.path.join(project_dir, project_name, 'draft_content.json')
        if not os.path.exists(draft_file):
            return "找不到工程文件"
            
        with open(draft_file, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
            
        # 创建文本ID到索引的映射
        text_id_to_index = {
            text['id']: i for i, text in enumerate(draft_data['materials']['texts'])
        }
        
        # 替换字体
        for replacement in text_replacements:
            text_id = replacement['text_id']
            font_path = replacement['font_path']
            
            if text_id in text_id_to_index:
                text_index = text_id_to_index[text_id]
                text = draft_data['materials']['texts'][text_index]
                
                # 更新字体相关属性
                text['font_path'] = font_path
                text['font_name'] = os.path.splitext(os.path.basename(font_path))[0]
                
                # 更新content中的字体信息
                content_data = json.loads(text['content'])
                for style in content_data.get('styles', []):
                    if 'font' in style:
                        style['font']['path'] = font_path
                text['content'] = json.dumps(content_data)
        
        # 保存修改后的文件
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=4)
            
        return None
    except Exception as e:
        return str(e)

@app.route('/replace_jianying_font', methods=['POST'])
def replace_jianying_font_route():
    """替换剪映项目字体的路由"""
    try:
        project_dir = request.form.get('project_dir')
        project_name = request.form.get('project_name')
        text_replacements = json.loads(request.form.get('text_replacements', '[]'))
        
        if not project_dir or not project_name:
            return jsonify({
                'success': False,
                'error': '请提供项目目录和工程名称'
            })
            
        if not text_replacements:
            return jsonify({
                'success': False,
                'error': '请选择要更换字体的文本'
            })
            
        error = replace_jianying_font(project_dir, project_name, text_replacements)
        if error:
            return jsonify({
                'success': False,
                'error': error
            })
            
        return jsonify({
            'success': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/font/<path:filename>')
def serve_font(filename):
    return send_from_directory('font', filename)

@app.route('/split_script', methods=['POST'])
def split_script():
    try:
        script_text = request.form.get('script_text')
        split_mode = request.form.get('split_mode', 'period')
        custom_split_chars = request.form.get('custom_split_chars', '')
        calculate_duration = request.form.get('calculate_duration', 'false').lower() == 'true'
        
        if not script_text:
            return jsonify({"error": "文案内容不能为空"}), 400
        
        # 根据切分模式选择切分字符
        split_chars = []
        if split_mode == 'period':
            split_chars = ['。', '！', '？', '!', '?', '.']
        elif split_mode == 'comma':
            split_chars = ['，', '；', ',', ';']
        elif split_mode == 'custom':
            if not custom_split_chars:
                return jsonify({"error": "自定义切分字符不能为空"}), 400
            split_chars = list(custom_split_chars)
        
        # 分割文本
        segments = []
        
        if split_mode == 'four':
            # 按四句一切分
            lines = [line.strip() for line in script_text.splitlines() if line.strip()]
            for i in range(0, len(lines), 4):
                chunk = lines[i:i+4]
                text = '\n'.join(chunk)
                
                duration = None
                if calculate_duration:
                    # 计算字符数（不含空白字符）
                    char_count = len(''.join(chunk).replace(' ', '').replace('\n', '').replace('\t', ''))
                    # 每个字0.3秒
                    duration = int(char_count * 0.3 * 1000000)  # 转换为微秒
                
                segments.append({
                    'text': text,
                    'duration': duration
                })
        else:
            # 按标点符号切分
            current_segment = ""
            
            for char in script_text:
                current_segment += char
                
                if char in split_chars:
                    # 处理切分后的文本段落
                    text = current_segment.strip()
                    if text:
                        duration = None
                        if calculate_duration:
                            # 计算字符数（不含空白字符）
                            char_count = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
                            # 每个字0.3秒
                            duration = int(char_count * 0.3 * 1000000)  # 转换为微秒
                        
                        segments.append({
                            'text': text,
                            'duration': duration
                        })
                    current_segment = ""
            
            # 处理最后一段文本（如果不以分隔符结尾）
            if current_segment.strip():
                text = current_segment.strip()
                duration = None
                if calculate_duration:
                    char_count = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
                    duration = int(char_count * 0.3 * 1000000)
                
                segments.append({
                    'text': text,
                    'duration': duration
                })
        
        return jsonify({
            "success": True,
            "segments": segments
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate_ai_script', methods=['POST'])
def generate_ai_script():
    try:
        prompt = request.form.get('prompt')
        if not prompt:
            return jsonify({"error": "提示词不能为空"}), 400
        
        # 获取API Key
        api_key = get_deepseek_api_key()
        if not api_key:
            return jsonify({"error": "请先设置DeepSeek API Key"}), 400
        
        # 调用DeepSeek API生成文案
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的文案撰写助手，请根据用户的要求创作高质量的文案。"},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        
        script = response.choices[0].message.content
        
        return jsonify({
            "success": True,
            "script": script
        })
    except Exception as e:
        return jsonify({"error": f"生成文案失败: {str(e)}"}), 500

@app.route('/save_deepseek_api_key', methods=['POST'])
def save_api_key_route():
    api_key = request.form.get('api_key')
    if not api_key:
        return jsonify({"error": "API Key不能为空"}), 400
    
    try:
        save_deepseek_api_key(api_key)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/import_script_to_jianying', methods=['POST'])
def import_script_to_jianying():
    try:
        project_dir = request.form.get('project_dir')
        project_name = request.form.get('project_name')
        segments_json = request.form.get('segments')
        font_size = float(request.form.get('font_size', 6.0))

        
        if not all([project_dir, project_name, segments_json]):
            return jsonify({"error": "缺少必要参数"}), 400
        
        # 解析段落数据
        try:
            segments = json.loads(segments_json)
        except:
            return jsonify({"error": "解析段落数据失败"}), 400
        
        if not segments:
            return jsonify({"error": "没有有效的文案段落"}), 400
        
        # 导入到剪映
        draft_file = os.path.join(project_dir, project_name, 'draft_content.json')
        if not os.path.exists(draft_file):
            return jsonify({"error": "找不到剪映项目文件"}), 400
        
        # 读取项目文件
        with open(draft_file, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
        
        # 备份原始文件
        backup_path = f"{draft_file}.scriptbak"
        shutil.copy(draft_file, backup_path)
        
        # 计算视频时间线总时长
        current_duration = draft_data.get('duration', 0)
        
        # 获取最后一个轨道元素的结束时间
        tracks = draft_data.get('tracks', [])
        text_track = None
        audio_track = None
        
        # 查找文本轨道和音频轨道
        for track in tracks:
            if track.get('type') == 'text':
                text_track = track
            elif track.get('type') == 'audio':
                audio_track = track
        
        # 如果没有文本轨道，创建一个
        if not text_track:
            text_track = {
                "attribute": 0,
                "flag": 0,
                "id": str(uuid.uuid4()).upper(),
                "is_default_name": True,
                "name": "",
                "segments": [],
                "type": "text"
            }
            tracks.append(text_track)
        
        # 如果没有音频轨道，创建一个
        if not audio_track:
            audio_track = {
                "attribute": 0,
                "flag": 0,
                "id": str(uuid.uuid4()).upper(),
                "is_default_name": True,
                "name": "",
                "segments": [],
                "type": "audio"
            }
            tracks.append(audio_track)
        
        # 找到最后一个元素的结束时间
        last_end_time = 0
        for track in tracks:
            for segment in track.get('segments', []):
                if 'target_timerange' in segment:
                    segment_end = segment['target_timerange']['start'] + segment['target_timerange']['duration']
                    if segment_end > last_end_time:
                        last_end_time = segment_end
        
        # 更新材料库
        materials = draft_data.get('materials', {})
        
        # 文本材料库
        texts = materials.get('texts', [])
        
        # 音频材料库
        audios = materials.get('audios', [])
        
        # 动画材料库
        animations = materials.get('material_animations', [])
        
        # 处理每个段落
        start_time = last_end_time
        text_segments = []
        audio_segments = []
        
        for segment in segments:
            text_content = segment.get('text', '').strip()
            if not text_content:
                continue
                
            # 获取时长（微秒）
            duration = segment.get('duration')
            if not duration:
                # 如果没有指定时长，按每字0.3秒计算
                char_count = len(text_content.replace(' ', '').replace('\n', '').replace('\t', ''))
                duration = int(char_count * 0.3 * 1000000)  # 转换为微秒
            
            # 创建新的文本ID
            text_id = str(uuid.uuid4()).upper()
            
            # 创建新的音频ID
            audio_id = str(uuid.uuid4()).upper()
            
            # 创建文本内容JSON
            #获取当前绝对路径
            current_path = os.path.abspath(os.path.dirname(__file__))
            #获取字体路径
            font_path=f"{current_path}/static/simkai.ttf"
            text_json = {
                "text": text_content,
                "styles": [{
                    "fill": {"content": {"solid": {"color": [1, 1, 1]}}},
                    "font": {"path": font_path, "id": ""},
                    "size": font_size,
                    "range": [0, len(text_content)]
                }]
            }
            
            # 添加到文本材料库
            text_item = {
                "add_type": 0,
                "alignment": 1,
                "background_alpha": 1,
                "background_color": "",
                "background_height": 0.14,
                "background_horizontal_offset": 0,
                "background_round_radius": 0,
                "background_style": 0,
                "background_vertical_offset": 0,
                "background_width": 0.14,
                "base_content": "",
                "bold_width": 0,
                "border_alpha": 1,
                "border_color": "",
                "border_width": 0.08,
                "caption_template_info": {},
                "check_flag": 7,
                "combo_info": {"text_templates": []},
                "content": json.dumps(text_json),
                "fixed_height": -1,
                "fixed_width": -1,
                "font_name": "zh-hans",
                "font_path": font_path,
                "font_size": "10.33333333333341",
                "global_alpha": 1,
                "id": text_id,
                "letter_spacing": 0,
                "line_feed": 1,
                "line_max_width": 0.82,
                "line_spacing": 0.02,
                "text_alpha": 1,
                "text_color": "#FFFFFF",
                "text_size": 30,
                "text_to_audio_ids": [audio_id],
                "type": "text"
            }
            
            texts.append(text_item)
            
            # 添加到音频材料库
            audio_path_dir = os.path.join(project_dir, project_name, 'textReading')
            #判断文件是否存在
            if not os.path.exists(audio_path_dir):
                os.makedirs(audio_path_dir)
            audio_path = f"{audio_path_dir}/{audio_id.lower()}.wav"
            audio_item = {
                "app_id": 0,
                "check_flag": 1,
                "duration": duration,
                "id": audio_id,
                "name": text_content[:20] + ("..." if len(text_content) > 20 else ""),
                "path": audio_path,
                "text_id": text_id,
                "type": "text_to_audio"
            }
            
            audios.append(audio_item)
            
            # 添加动画
            animation_id = str(uuid.uuid4()).upper()
            animation_item = {
                "animations": [],
                "id": animation_id,
                "multi_language_current": "none",
                "type": "sticker_animation"
            }
            
            animations.append(animation_item)
            
            # 添加到轨道
            text_segment = {
                "caption_info": None,
                "cartoon": False,
                "clip": {
                    "alpha": 1,
                    "flip": {"horizontal": False, "vertical": False},
                    "rotation": 0,
                    "scale": {"x": 1, "y": 1},
                    "transform": {"x": 0, "y": -0.7721662468513853}
                },
                "common_keyframes": [],
                "enable_adjust": False,
                "extra_material_refs": [animation_id],
                "group_id": "",
                "id": str(uuid.uuid4()).upper(),
                "material_id": text_id,
                "render_index": 14000 + len(text_segments),
                "target_timerange": {
                    "duration": duration,
                    "start": start_time
                },
                "track_attribute": 0,
                "track_render_index": 1,
                "uniform_scale": {"on": True, "value": 1},
                "visible": True,
                "volume": 1
            }
            
            audio_segment = {
                "caption_info": None,
                "cartoon": False,
                "clip": None,
                "common_keyframes": [],
                "enable_adjust": False,
                "group_id": "",
                "id": str(uuid.uuid4()).upper(),
                "material_id": audio_id,
                "render_index": 0,
                "source_timerange": {
                    "duration": duration,
                    "start": 0
                },
                "target_timerange": {
                    "duration": duration,
                    "start": start_time
                },
                "track_attribute": 0,
                "track_render_index": 0,
                "visible": True,
                "volume": 1
            }
            
            text_segments.append(text_segment)
            audio_segments.append(audio_segment)
            
            # 更新下一段的开始时间
            start_time += duration
        
        # 将新段落添加到轨道
        text_track['segments'].extend(text_segments)
        audio_track['segments'].extend(audio_segments)
        
        # 更新材料库
        materials['texts'] = texts
        materials['audios'] = audios
        materials['material_animations'] = animations
        
        # 更新草稿总时长
        if start_time > current_duration:
            draft_data['duration'] = start_time
        
        # 保存更新后的项目文件
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=4)
        
        return jsonify({
            "success": True,
            "message": f"成功导入{len(segments)}个文案段落"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
def check_jianying_path():
    # 获取当前用户的AppData目录
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        if config["jianying_project_dir"]=="":
            print("正在自动获取剪映路径")

        else:
            print(f"config.json jianying_project_dir已有值，跳过处理,{config['jianying_project_dir']}")
            return ""
    else:
        print("config.json不存在，正在创建")
        config = {
            "jianying_project_dir": ""
        }
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    try:
        appdata_path = os.getenv('LOCALAPPDATA')
        if not appdata_path:
            return False

        # 构造剪映项目路径
        jianying_path = os.path.join(
            appdata_path,
            'JianyingPro',
            'User Data',
            'Projects',
            'com.lveditor.draft'
        )

        # 检查路径是否存在
        config["jianying_project_dir"]=jianying_path
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return os.path.exists(jianying_path)
    except:
        print("Windown没有该目录,若是其他系统,请自行在填写网页中填写")

@app.route('/get_categories', methods=['GET'])
def get_categories():
    """获取所有音频分类"""
    categories = load_voice_categories()
    return jsonify(categories)

# 工具函数：根据分类名称自动生成ID
def generate_category_id(name):
    # 保留字母、数字、下划线、CJK（中日韩）字符，其余替换为下划线
    # CJK范围：\u4e00-\u9fff（中日汉字），\u3040-\u30ff（日文假名），\uac00-\ud7af（韩文）
    id = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]', '_', name)
    id = id.lower()
    id = re.sub(r'_+', '_', id)
    id = id.strip('_')
    return id

@app.route('/add_category', methods=['POST'])
def add_category_route():
    """添加新的音频分类"""
    # category_id = request.form.get('category_id')  # 不再从前端获取
    category_name = request.form.get('category_name')
    description = request.form.get('description', '')
    
    if not category_name:
        return jsonify({"error": "缺少必要参数"}), 400
    
    # 自动生成分类ID
    category_id = generate_category_id(category_name)
    if not category_id:
        return jsonify({"error": "分类名称无有效字符，无法生成ID"}), 400
    
    success, message = add_voice_category(category_id, category_name, description)
    
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"error": message}), 400

@app.route('/delete_category', methods=['POST'])
def delete_category_route():
    """删除音频分类"""
    category_id = request.form.get('category_id')
    
    if not category_id:
        return jsonify({"error": "缺少必要参数"}), 400
    
    success, message = delete_voice_category(category_id)
    
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"error": message}), 400

@app.route('/upload_audio', methods=['POST'])
def upload_audio_route():
    """上传音频文件"""
    category_id = request.form.get('category_id')
    
    if 'audio_file' not in request.files:
        return jsonify({"error": "未上传文件"}), 400
    
    audio_file = request.files['audio_file']
    
    if audio_file.filename == '':
        return jsonify({"error": "未选择文件"}), 400
    
    if not category_id:
        category_id = "other"  # 默认分类
    
    # 检查文件类型，如果不是支持的格式，尝试转换
    original_filename = audio_file.filename
    name, ext = os.path.splitext(original_filename)
    ext = ext.lower()  # 扩展名转为小写
    # 替换不安全的字符，但保留中文
    safe_filename = ""
    for char in name:
        if char.isalnum() or char in '._- ' or '\u4e00' <= char <= '\u9fff':  # 保留字母数字和中文字符
            safe_filename += char
        else:
            safe_filename += '_'
    filename = safe_filename + ext
    
    # 如果分类不存在，使用other
    category_path = os.path.join(VOICE_DIR, category_id)
    if not os.path.exists(category_path):
        category_id = "other"
        category_path = os.path.join(VOICE_DIR, "other")
    
    # 保存文件
    file_path = os.path.join(category_path, filename)
    audio_file.save(file_path)
    
    # 更新data.json
    voice_data, data_file = load_voice_data()
    voice_url = f"voice/{category_id}/{filename}"
    voice_data[filename] = {
        "note": "",
        "path": voice_url,
        "category": category_id
    }
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(voice_data, f, ensure_ascii=False, indent=2)
    
    return True, "音频文件上传成功"

@app.route('/batch_upload_audio', methods=['POST'])
def batch_upload_audio_route():
    """批量上传音频文件"""
    category_id = request.form.get('category_id')
    
    if 'audio_files[]' not in request.files:
        return jsonify({"error": "未上传文件"}), 400
    
    audio_files = request.files.getlist('audio_files[]')
    
    if not audio_files or all(file.filename == '' for file in audio_files):
        return jsonify({"error": "未选择文件"}), 400
    
    if not category_id:
        category_id = "other"  # 默认分类
    
    # 批量上传
    result = batch_upload_audio_files(audio_files, category_id)
    
    # 重新加载语音列表
    voices = load_all_voices()
    
    return jsonify({
        "success": True,
        "message": f"上传完成: 成功 {result['success_count']} 个, 失败 {result['failed_count']} 个",
        "details": result['results'],
        "voices": voices
    })

@app.route('/delete_audio', methods=['POST'])
def delete_audio_route():
    """删除音频文件"""
    filename = request.form.get('filename')
    
    if not filename:
        return jsonify({"error": "未指定文件名"}), 400
    
    success, message = delete_audio_file(filename)
    
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"error": message}), 400

if __name__ == '__main__':
    # 确保输出目录存在
    os.makedirs(os.path.join("static", "output"), exist_ok=True)
    
    # 确保临时目录存在并清空临时文件
    os.makedirs(TEMP_DIR, exist_ok=True)
    try:
        # 清空临时目录中的所有文件
        for file in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"无法删除临时文件 {file_path}: {str(e)}")
    except Exception as e:
        print(f"清空临时目录失败: {str(e)}")
    
    # 检查必要的依赖项
    try:
        import pydub
        print("已安装音频处理库 pydub")
    except ImportError:
        print("警告: 未安装音频处理库 pydub，将无法进行音频格式转换")
        print("请运行: pip install pydub")
        
        # 检查ffmpeg
        try:
            from pydub.utils import which
            if which("ffmpeg") is None:
                print("警告: 未安装 ffmpeg，这是音频转换所必需的")
                print("请安装 ffmpeg: https://ffmpeg.org/download.html")
        except:
            print("警告: 请确保已安装 ffmpeg: https://ffmpeg.org/download.html")
    
    import webbrowser
    webbrowser.open("http://localhost:5000")
    check_jianying_path()
    app.run()