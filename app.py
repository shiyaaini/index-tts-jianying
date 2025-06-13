import os
import json
import uuid
import datetime
import time
import shutil
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import glob

from indextts.infer import IndexTTS

app = Flask(__name__)

# 配置文件路径
CONFIG_FILE = "config.json"

# 生成记录文件路径
HISTORY_FILE = "records/generation_history.json"

# 添加字体目录配置
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'font')

# 确保记录目录存在
os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

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

# 加载特定模型的参考音频列表
def load_voices(model_path):
    voices = []
    voice_dir = os.path.join(model_path, "voice")
    data_file = os.path.join(voice_dir, "data.json")
    
    # 确保data.json文件存在
    if not os.path.exists(data_file):
        # 如果不存在，创建一个默认的data.json
        create_default_data_json(voice_dir)
    
    # 加载data.json
    with open(data_file, "r", encoding="utf-8") as f:
        try:
            voice_data = json.load(f)
        except json.JSONDecodeError:
            # 如果JSON格式有误，创建一个空字典
            voice_data = {}
    
    # 扫描voice目录下的所有音频文件
    for file in os.listdir(voice_dir):
        if file.endswith((".wav", ".mp3")):
            # 如果在data.json中有记录，使用记录的备注
            if file in voice_data:
                note = voice_data[file].get("note", "")
            else:
                # 如果没有记录，添加一个空备注
                note = ""
                voice_data[file] = {"note": note, "path": os.path.join(voice_dir, file)}
                # 更新data.json
                with open(data_file, "w", encoding="utf-8") as f:
                    json.dump(voice_data, f, ensure_ascii=False, indent=2)
            
            voices.append({
                "name": file,
                "note": note,
                "path": os.path.join(voice_dir, file)
            })
    
    return voices

# 创建默认的data.json文件
def create_default_data_json(voice_dir):
    if not os.path.exists(voice_dir):
        os.makedirs(voice_dir)
    
    data_file = os.path.join(voice_dir, "data.json")
    default_data = {}
    
    # 扫描voice目录下的所有音频文件，如果有的话
    if os.path.exists(voice_dir):
        for file in os.listdir(voice_dir):
            if file.endswith((".wav", ".mp3")):
                default_data[file] = {
                    "note": "",
                    "path": os.path.join(voice_dir, file)
                }
    
    # 写入默认data.json
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(default_data, f, ensure_ascii=False, indent=2)

# 更新参考音频备注
def update_voice_note(model_path, voice_name, note):
    voice_dir = os.path.join(model_path, "voice")
    data_file = os.path.join(voice_dir, "data.json")
    
    # 确保data.json文件存在
    if not os.path.exists(data_file):
        create_default_data_json(voice_dir)
    
    # 加载data.json
    with open(data_file, "r", encoding="utf-8") as f:
        try:
            voice_data = json.load(f)
        except json.JSONDecodeError:
            voice_data = {}
    
    # 更新备注
    if voice_name in voice_data:
        voice_data[voice_name]["note"] = note
    else:
        voice_data[voice_name] = {
            "note": note,
            "path": os.path.join(voice_dir, voice_name)
        }
    
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

@app.route('/')
def index():
    models = load_models()
    # 默认选择第一个模型
    default_model = models[0]["path"] if models else ""
    # 加载默认模型的参考音频
    voices = load_voices(default_model) if default_model else []
    # 加载生成历史记录
    history = load_history()
    # 加载配置信息
    config = load_config()
    jianying_project_dir = config.get("jianying_project_dir", "")
    
    return render_template('index.html', 
                          models=models, 
                          voices=voices, 
                          selected_model=default_model, 
                          history=history,
                          jianying_project_dir=jianying_project_dir)

@app.route('/get_voices', methods=['GET'])
def get_voices():
    model_path = request.args.get('model_path')
    if not model_path:
        return jsonify({"error": "未指定模型路径"}), 400
    
    voices = load_voices(model_path)
    return jsonify(voices)

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
    model_path = request.form.get('model_path')
    voice_name = request.form.get('voice_name')
    note = request.form.get('note')
    
    if not model_path or not voice_name:
        return jsonify({"error": "请指定模型路径和音频名称"}), 400
    
    update_voice_note(model_path, voice_name, note)
    return jsonify({"success": True})

@app.route('/audio/<path:filename>')
def get_audio(filename):
    return send_file(filename)

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

# 加载剪映项目中的音频信息
def load_jianying_audio_info(project_dir, project_name):
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
                text_content = content_data.get("text", "")
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
def replace_jianying_audio(project_dir, project_name, audio_replacements):
    """
    替换剪映项目中的多个音频
    
    :param project_dir: 剪映项目目录
    :param project_name: 项目名称
    :param audio_replacements: 音频替换数据列表，每项包含 audio_id、new_audio_path、duration
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
            'path': item['new_audio_path'], 
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
    
    if not project_dir or not project_name:
        return jsonify({"error": "缺少必要参数"}), 400
    
    success, result = load_jianying_audio_info(project_dir, project_name)
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
                
                # 添加到替换列表
                audio_replacements.append({
                    'audio_id': audio_id,
                    'new_audio_path': output_path,
                    'duration': duration_us
                })
                
                results.append({
                    "id": audio_id,
                    "success": True,
                    "output_file": output_path,
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
            success, message = replace_jianying_audio(project_dir, project_name, audio_replacements)
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

if __name__ == '__main__':
    # 确保输出目录存在
    os.makedirs(os.path.join("static", "output"), exist_ok=True)
    app.run(debug=True) 