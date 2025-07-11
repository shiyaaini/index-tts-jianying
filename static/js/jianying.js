// 剪映音频替换功能相关的JavaScript代码
$(document).ready(function() {
    let selectedProject = '';
    let projectAudios = [];
    
    // 初始化时设置默认值
    function initSelectedVoice() {
        // 获取表格中第一个选中的音频路径
        const firstCheckedVoice = $('#jianyingVoiceTable tbody tr input[type="radio"]:checked').closest('tr');
        if (firstCheckedVoice.length > 0) {
            const voicePath = firstCheckedVoice.data('voice-path');
            $('#jianyingSelectedVoice').val(voicePath);
            console.log('初始化选择音频:', voicePath);
        }
    }
    
    // 页面加载完成后初始化
    initSelectedVoice();
    
    // 切换模型时更新参考音频列表
    $('#jianyingModelSelect').on('change', function() {
        const modelPath = $(this).val();
        
        // 显示加载状态
        $('#jianyingVoiceTable tbody').html('<tr><td colspan="6" class="text-center">加载中...</td></tr>');
        
        // 请求该模型的参考音频列表
        $.get('/get_voices', { model_path: modelPath }, function(response) {
            let voicesHtml = '';
            const voices = response.voices || [];
            
            if (voices.length === 0) {
                voicesHtml = '<tr><td colspan="6" class="text-center">没有可用的参考音频</td></tr>';
                $('#jianyingSelectedVoice').val(''); // 清空选择
            } else {
                voices.forEach((voice, index) => {
                    voicesHtml += `
                        <tr data-voice-path="${voice.path}" data-voice-name="${voice.name}" data-category="${voice.category}" class="voice-row">
                            <td><input type="radio" name="jianyingVoiceRadio" class="form-check-input" ${index === 0 ? 'checked' : ''}></td>
                            <td>${voice.name}</td>
                            <td>
                                <audio src="/audio/${voice.path}" controls class="audio-player w-100"></audio>
                            </td>
                            <td>
                                <input type="text" class="form-control voice-note-input" value="${voice.note}" placeholder="添加备注">
                            </td>
                            <td>
                                <select class="form-select form-select-sm voice-category-select">
                                    ${response.categories ? response.categories.map(cat => 
                                        `<option value="${cat.id}" ${voice.category === cat.id ? 'selected' : ''}>${cat.name}</option>`
                                    ).join('') : ''}
                                </select>
                            </td>
                            <td>
                                <button type="button" class="btn btn-sm btn-outline-primary save-note-btn">保存备注</button>
                            </td>
                        </tr>
                    `;
                });
                
                // 选中第一个音频作为默认值
                if (voices.length > 0) {
                    $('#jianyingSelectedVoice').val(voices[0].path);
                    console.log('设置默认音频:', voices[0].path);
                }
            }
            
            $('#jianyingVoiceTable tbody').html(voicesHtml);
            
            // 重新绑定音频选择事件
            bindJianyingVoiceEvents();
        });
    });
    
    // 绑定参考音频选择事件
    function bindJianyingVoiceEvents() {
        // 选择参考音频
        $('#jianyingVoiceTable tbody tr input[type="radio"]').on('change', function() {
            const voicePath = $(this).closest('tr').data('voice-path');
            $('#jianyingSelectedVoice').val(voicePath);
            console.log('选择音频:', voicePath);
        });
        
        // 保存备注
        $('#jianyingVoiceTable .save-note-btn').on('click', function() {
            const row = $(this).closest('tr');
            const voiceName = row.data('voice-name');
            const note = row.find('.voice-note-input').val();
            const modelPath = $('#jianyingModelSelect').val();
            
            $.post('/update-note', {
                model_path: modelPath,
                voice_name: voiceName,
                note: note
            }, function(response) {
                if (response.success) {
                    // 显示成功消息
                    alert('备注已保存');
                }
            });
        });
        
        // 分类筛选功能 - 剪映面板专用
        $('#jianyingPanel .category-badge').off('click').on('click', function() {
            // 移除所有分类的active状态
            $('#jianyingPanel .category-badge').removeClass('active');
            
            // 添加当前分类的active状态
            $(this).addClass('active');
            
            // 获取选择的分类
            const selectedCategory = $(this).data('category');
            
            // 筛选表格行
            if (selectedCategory === 'all') {
                $('#jianyingVoiceTable .voice-row').removeClass('filtered').show();
            } else {
                $('#jianyingVoiceTable .voice-row').each(function() {
                    const rowCategory = $(this).data('category');
                    if (rowCategory === selectedCategory) {
                        $(this).removeClass('filtered').show();
                    } else {
                        $(this).addClass('filtered').hide();
                    }
                });
            }
        });
    }
    
    // 初始化绑定参考音频事件
    bindJianyingVoiceEvents();
    
    // 检查项目目录按钮点击事件
    $('#checkProjectBtn').on('click', function() {
        const projectDir = $('#projectPath').val().trim();
        
        if (!projectDir) {
            $('#jianyingErrorArea').text('请输入剪映项目目录路径').show();
            $('#jianyingSuccessArea').hide();
            return;
        }
        
        // 显示加载状态
        $('#jianyingLoadingArea').show();
        $('#jianyingErrorArea').hide();
        $('#jianyingSuccessArea').hide();
        
        // 检查项目目录
        $.post('/check_jianying_project', {
            project_dir: projectDir
        }, function(response) {
            $('#jianyingLoadingArea').hide();
            
            if (response.success && response.projects.length > 0) {
                // 填充工程选择下拉框
                let options = '';
                response.projects.forEach(project => {
                    options += `<option value="${project}">${project}</option>`;
                });
                
                $('#projectSelect').html(options);
                $('#projectSelectContainer').show();
                $('#jianyingSuccessArea').text(`成功找到 ${response.projects.length} 个剪映工程`).show();
            } else {
                $('#jianyingErrorArea').text('未找到有效的剪映项目').show();
                $('#projectSelectContainer').hide();
            }
        }).fail(function(xhr) {
            $('#jianyingLoadingArea').hide();
            $('#jianyingErrorArea').text(xhr.responseJSON?.error || '加载项目失败').show();
            $('#projectSelectContainer').hide();
        });
    });
    
    // 加载项目按钮点击事件
    $('#loadProjectBtn').on('click', function() {
        const projectDir = $('#projectPath').val().trim();
        selectedProject = $('#projectSelect').val();
        let getAllSubtitles = $('#loadAllSubtitlesCheckbox').is(':checked');
        
        if (!projectDir || !selectedProject) {
            $('#jianyingErrorArea').text('请确保已选择项目目录和工程').show();
            $('#jianyingSuccessArea').hide();
            return;
        }
        
        // 显示加载状态
        $('#jianyingLoadingArea').show();
        $('#jianyingErrorArea').hide();
        $('#jianyingSuccessArea').hide();
        
        loadProjectAudio(projectDir, selectedProject, getAllSubtitles);
    });
    
    // 加载项目音频
    function loadProjectAudio(projectDir, projectName,get_all_subtitles = false) {
        $.post('/load_jianying_audio', {
            project_dir: projectDir,
            project_name: projectName,
            get_all_subtitles: get_all_subtitles
        }, function(response) {
            $('#jianyingLoadingArea').hide();
            
            if (response.success && response.audio_infos.length > 0) {
                projectAudios = response.audio_infos;
                displayProjectAudios(projectAudios);
                $('#jianyingSuccessArea').text(`成功加载项目"${projectName}"中的${projectAudios.length}个音频`).show();
                $('#replaceAudioBtn').show();
            } else if (response.success) {
                $('#jianyingErrorArea').text('项目中没有可替换的音频').show();
                $('#projectAudioList').hide();
                $('#replaceAudioBtn').hide();
            }
        }).fail(function(xhr) {
            $('#jianyingLoadingArea').hide();
            $('#jianyingErrorArea').text(xhr.responseJSON?.error || '加载项目音频失败').show();
        });
    }
    
    // 显示项目音频列表
    function displayProjectAudios(audios) {
        let audioListHtml = '';
        
        audios.forEach((audio, index) => {
            // 显示音频替换状态
            const statusHtml = audio.status ? 
                '<span class="badge bg-success">已替换</span>' : 
                '<span class="badge bg-secondary">未替换</span>';
            
            // 检查音频文件是否存在
            let audioPlayerHtml = '';
            if (audio.file_exists) {
                audioPlayerHtml = `<audio src="/audio/${audio.path}" controls class="audio-player w-100"></audio>`;
            } else {
                audioPlayerHtml = `<div class="alert alert-warning p-1 mb-0 text-center">音频文件不存在</div>`;
            }
            
            audioListHtml += `
                <tr data-audio-id="${audio.id}" data-text-id="${audio.text_id}">
                    <td><input type="checkbox" class="form-check-input audio-select-checkbox" value="${audio.id}"></td>
                    <td>${audio.name}</td>
                    <td>
                        ${audioPlayerHtml}
                    </td>
                    <td>
                        <textarea class="form-control audio-text" rows="2" data-original-text="${audio.text_content}">${audio.text_content}</textarea>
                    </td>
                    <td class="text-center">
                        ${statusHtml}
                    </td>
                    <td>
                        <button type="button" class="btn btn-sm btn-outline-success save-text-btn" title="保存文本">
                            保存文本
                        </button>
                    </td>
                </tr>
            `;
        });
        
        $('#audioListBody').html(audioListHtml);
        $('#projectAudioList').show();
        
        // 绑定全选/取消全选
        $('#selectAllAudios').on('change', function() {
            $('.audio-select-checkbox').prop('checked', $(this).is(':checked'));
        });
        
        // 绑定保存文本按钮点击事件
        $('.save-text-btn').on('click', function() {
            const row = $(this).closest('tr');
            const textArea = row.find('.audio-text');
            const newText = textArea.val();
            const originalText = textArea.data('original-text');
            const audioId = row.data('audio-id');
            const textId = row.data('text-id');
            
            if (newText === originalText) {
                alert('文本内容未修改');
                return;
            }
            
            if (confirm('确定要保存修改后的文本内容吗？')) {
                // 显示加载状态
                $('#jianyingLoadingArea').show();
                
                // 发送保存请求
                $.post('/save_jianying_text', {
                    project_dir: $('#projectPath').val().trim(),
                    project_name: selectedProject,
                    text_id: textId,
                    audio_id: audioId,
                    text_content: newText
                }, function(response) {
                    $('#jianyingLoadingArea').hide();
                    
                    if (response.success) {
                        // 更新数据属性
                        textArea.data('original-text', newText);
                        alert('文本保存成功');
                    } else {
                        alert('保存失败：' + response.error);
                    }
                }).fail(function(xhr) {
                    $('#jianyingLoadingArea').hide();
                    alert('保存请求失败：' + (xhr.responseJSON?.error || '未知错误'));
                });
            }
        });
    }
    
    // 替换音频按钮点击事件
    $('#jianyingForm').on('submit', function(e) {
        e.preventDefault();
        
        const selectedAudios = $('.audio-select-checkbox:checked');
        
        if (selectedAudios.length === 0) {
            $('#jianyingErrorArea').text('请选择要替换的音频').show();
            $('#jianyingSuccessArea').hide();
            return;
        }
        
        // 检查是否选择了参考音频
        const selectedVoice = $('#jianyingSelectedVoice').val();
        if (!selectedVoice) {
            $('#jianyingErrorArea').text('请选择参考音频').show();
            $('#jianyingSuccessArea').hide();
            return;
        }
        
        // 收集所有选中的音频数据
        const audioItems = [];
        selectedAudios.each(function() {
            const audioId = $(this).val();
            const row = $(this).closest('tr');
            const text = row.find('.audio-text').val();
            
            if (text) {
                audioItems.push({
                    id: audioId,
                    text: text
                });
            }
        });
        
        if (audioItems.length === 0) {
            $('#jianyingErrorArea').text('所有选中的音频文本内容都为空').show();
            $('#jianyingSuccessArea').hide();
            return;
        }
        
        // 准备请求数据
        const requestData = {
            project_dir: $('#projectPath').val().trim(),
            project_name: selectedProject,
            audio_data: JSON.stringify(audioItems),
            model: $('#jianyingModelSelect').val(),
            voice: selectedVoice,
            sync_position: $('#syncPositionCheck').is(':checked'),
            append_to_last: $('#appendToLastCheck').is(':checked')
        };
        
        console.log('提交请求数据:', requestData);
        
        // 显示加载状态
        $('#jianyingLoadingArea').show();
        $('#jianyingErrorArea').hide();
        $('#jianyingSuccessArea').hide();
        
        // 发送替换请求
        $.post('/replace_jianying_audio', requestData, function(response) {
            $('#jianyingLoadingArea').hide();
            
            if (response.success) {
                $('#jianyingSuccessArea').html(`
                    <div class="alert alert-success">
                        ${response.message}，生成耗时${response.generation_time}秒
                    </div>
                `).show();
                
                // 处理每个音频的结果
                if (response.results && response.results.length > 0) {
                    let resultsHtml = '<div class="mt-3"><h6>处理结果：</h6><ul class="list-group">';
                    
                    response.results.forEach(result => {
                        if (result.success) {
                            resultsHtml += `
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <span>ID: ${result.id.substring(0, 8)}... 处理成功</span>
                                    <span class="badge bg-success">成功</span>
                                </li>
                            `;
                            
                            // 更新状态显示
                            $(`tr[data-audio-id="${result.id}"] td:nth-child(5)`).html('<span class="badge bg-success">已替换</span>');
                        } else {
                            resultsHtml += `
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <span>ID: ${result.id ? result.id.substring(0, 8) + '...' : '未知'} 处理失败: ${result.message}</span>
                                    <span class="badge bg-danger">失败</span>
                                </li>
                            `;
                        }
                    });
                    
                    resultsHtml += '</ul></div>';
                    $('#jianyingSuccessArea').append(resultsHtml);
                }
            }
        }).fail(function(xhr) {
            $('#jianyingLoadingArea').hide();
            $('#jianyingErrorArea').text(xhr.responseJSON?.error || '替换音频失败').show();
        });
    });
    
    // 浏览按钮功能 (仅提示，实际上浏览器安全限制不允许直接选择文件夹)
    $('#browseBtn').on('click', function() {
        alert('由于浏览器安全限制，无法直接浏览文件夹。请手动输入剪映项目路径，一般位于：C:\\Users\\用户名\\AppData\\Local\\JianyingPro\\User Data\\Projects\\com.lveditor.draft');
    });
}); 