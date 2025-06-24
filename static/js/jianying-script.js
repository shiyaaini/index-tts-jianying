/**
 * 剪映文案功能相关脚本
 */
$(document).ready(function() {
    // 浏览项目目录按钮
    $('#scriptBrowseBtn').click(function() {
        browseFolder('#scriptProjectPath');
    });

    // 检查项目按钮点击事件
    $('#scriptCheckProjectBtn').click(function() {
        checkJianyingProject('#scriptProjectPath', '#scriptProjectSelect', '#scriptProjectSelectContainer');
    });

    // 加载工程
    $('#loadScriptProjectBtn').click(function() {
        loadScriptProject();
    });

    // 保存API Key
    $('#saveApiKeyBtn').click(function() {
        saveApiKey();
    });

    // 生成AI文案
    $('#generateAiScriptBtn').click(function() {
        generateAiScript();
    });

    // 切分文本按钮
    $('#splitScriptBtn').click(function() {
        splitScript();
    });

    // 导入到剪映按钮
    $('#importScriptBtn').click(function() {
        importScriptToJianying();
    });

    // 切分方式改变时，显示/隐藏自定义切分字符输入框
    $('input[name="scriptSplitMode"]').change(function() {
        if($(this).val() === 'custom') {
            $('#customSplitContainer').show();
        } else {
            $('#customSplitContainer').hide();
        }
    });
    
    // 字体大小选择改变时，显示/隐藏自定义字体大小输入框
    $('#fontSizeSelect').change(function() {
        if($(this).val() === 'custom') {
            $('#customFontSizeContainer').show();
        } else {
            $('#customFontSizeContainer').hide();
        }
    });
});

/**
 * 检查剪映项目并加载项目列表
 */
function checkJianyingProject(projectPathSelector, projectSelectSelector, containerSelector) {
    const projectDir = $(projectPathSelector).val().trim();
    
    if (!projectDir) {
        showError('scriptErrorArea', '请输入剪映项目目录路径');
        return;
    }
    
    $('#scriptLoadingArea').show();
    $('#scriptErrorArea').hide();
    
    $.ajax({
        url: '/check_jianying_project',
        type: 'POST',
        data: {
            project_dir: projectDir
        },
        success: function(response) {
            $('#scriptLoadingArea').hide();
            if (response.success) {
                // 填充项目选择下拉框
                const projectSelect = $(projectSelectSelector);
                projectSelect.empty();
                
                response.projects.forEach(function(project) {
                    projectSelect.append($('<option></option>').val(project).text(project));
                });
                
                // 显示项目选择区域
                $(containerSelector).show();
            } else {
                showError('scriptErrorArea', response.error || '检查项目失败');
            }
        },
        error: function(xhr) {
            $('#scriptLoadingArea').hide();
            const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : '服务器错误，请重试';
            showError('scriptErrorArea', errorMsg);
        }
    });
}

/**
 * 加载剪映项目
 */
function loadScriptProject() {
    const projectDir = $('#scriptProjectPath').val().trim();
    const projectName = $('#scriptProjectSelect').val();
    
    if (!projectDir || !projectName) {
        showError('scriptErrorArea', '请选择剪映项目');
        return;
    }
    
    $('#scriptLoadingArea').show();
    $('#scriptErrorArea').hide();
    $('#scriptSuccessArea').hide();
    
    $.ajax({
        url: '/load_jianying_text',
        type: 'POST',
        data: {
            project_dir: projectDir,
            project_name: projectName
        },
        success: function(response) {
            $('#scriptLoadingArea').hide();
            if (response.success) {
                // 如果返回了文本内容，直接处理并显示在切分结果中
                if (response.texts && response.texts.length > 0) {
                    const segments = [];
                    
                    response.texts.forEach(function(textItem) {
                        try {
                            // 解析content中的JSON字符串
                            const contentObj = JSON.parse(textItem.content);
                            if (contentObj.text) {
                                segments.push({
                                    text: contentObj.text,
                                    duration: null,
                                    font_size: textItem.font_size || 6.0
                                });
                            }
                        } catch (e) {
                            console.error('解析文本内容失败:', e);
                        }
                    });
                    
                    if (segments.length > 0) {
                        // 直接显示在切分结果中
                        displayScriptSegments(segments);
                        showSuccess('scriptSuccessArea', '工程文本加载成功');
                    } else {
                        showError('scriptErrorArea', '未找到有效的文本内容');
                    }
                } else {
                    showError('scriptErrorArea', '未找到文本内容');
                }
            } else {
                showError('scriptErrorArea', response.error || '加载项目失败');
            }
        },
        error: function(xhr) {
            $('#scriptLoadingArea').hide();
            const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : '服务器错误，请重试';
            showError('scriptErrorArea', errorMsg);
        }
    });
}

/**
 * 保存DeepSeek API Key
 */
function saveApiKey() {
    const apiKey = $('#deepseekApiKey').val().trim();
    
    if (!apiKey) {
        showError('scriptErrorArea', '请输入API Key');
        return;
    }
    
    $('#scriptLoadingArea').show();
    $('#scriptErrorArea').hide();
    $('#scriptSuccessArea').hide();
    
    $.ajax({
        url: '/save_deepseek_api_key',
        type: 'POST',
        data: {
            api_key: apiKey
        },
        success: function(response) {
            $('#scriptLoadingArea').hide();
            if (response.success) {
                showSuccess('scriptSuccessArea', 'API Key保存成功');
            } else {
                showError('scriptErrorArea', response.error || '保存API Key失败');
            }
        },
        error: function(xhr) {
            $('#scriptLoadingArea').hide();
            const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : '服务器错误，请重试';
            showError('scriptErrorArea', errorMsg);
        }
    });
}

/**
 * 生成AI文案
 */
function generateAiScript() {
    const prompt = $('#aiScriptPrompt').val().trim();
    
    if (!prompt) {
        showError('scriptErrorArea', '请输入AI提示词');
        return;
    }
    
    $('#scriptLoadingArea').show();
    $('#scriptErrorArea').hide();
    $('#scriptSuccessArea').hide();
    
    $.ajax({
        url: '/generate_ai_script',
        type: 'POST',
        data: {
            prompt: prompt
        },
        success: function(response) {
            $('#scriptLoadingArea').hide();
            if (response.success) {
                // 将生成的文案填入文本框
                $('#scriptTextarea').val(response.script);
                // 触发文本框自适应高度
                $('#scriptTextarea').trigger('input');
                showSuccess('scriptSuccessArea', 'AI文案生成成功');
            } else {
                showError('scriptErrorArea', response.error || 'AI文案生成失败');
            }
        },
        error: function(xhr) {
            $('#scriptLoadingArea').hide();
            const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : '服务器错误，请重试';
            showError('scriptErrorArea', errorMsg);
        }
    });
}

/**
 * 切分文本
 */
function splitScript() {
    const scriptText = $('#scriptTextarea').val().trim();
    
    if (!scriptText) {
        showError('scriptErrorArea', '请输入文案内容');
        return;
    }
    
    const splitMode = $('input[name="scriptSplitMode"]:checked').val();
    const calculateDuration = $('#calculateDurationByChar').is(':checked');
    const customSplitChars = $('#customSplitChars').val();
    const msPerChar = $('#msPerChar').val();
    
    // 检查自定义切分模式是否有输入切分字符
    if (splitMode === 'custom' && !customSplitChars) {
        showError('scriptErrorArea', '请输入自定义切分字符');
        return;
    }
    
    $('#scriptLoadingArea').show();
    $('#scriptErrorArea').hide();
    $('#scriptSuccessArea').hide();
    
    $.ajax({
        url: '/split_script',
        type: 'POST',
        data: {
            script_text: scriptText,
            split_mode: splitMode,
            custom_split_chars: customSplitChars,
            calculate_duration: calculateDuration,
            ms_per_char: msPerChar
        },
        success: function(response) {
            $('#scriptLoadingArea').hide();
            if (response.success) {
                // 展示切分结果
                displayScriptSegments(response.segments);
                showSuccess('scriptSuccessArea', '文案切分成功');
            } else {
                showError('scriptErrorArea', response.error || '文案切分失败');
            }
        },
        error: function(xhr) {
            $('#scriptLoadingArea').hide();
            const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : '服务器错误，请重试';
            showError('scriptErrorArea', errorMsg);
        }
    });
}

/**
 * 展示切分结果
 */
function displayScriptSegments(segments) {
    const tbody = $('#scriptSegmentsBody');
    tbody.empty();
    
    segments.forEach(function(segment, index) {
        const row = $('<tr></tr>');
        
        // 序号列
        row.append($('<td></td>').text(index + 1));
        
        // 文本内容列
        const textCell = $('<td></td>');
        const textArea = $('<textarea></textarea>')
            .addClass('form-control segment-text auto-resize')
            .attr('rows', Math.min(3, Math.ceil(segment.text.length / 30)))
            .val(segment.text)
            .data('index', index);
        textCell.append(textArea);
        row.append(textCell);
        
        // 预计时长列
        row.append($('<td></td>')
            .addClass('segment-duration')
            .text(segment.duration ? formatDuration(segment.duration) : '--'));
        
        tbody.append(row);
    });
    
    // 显示切分结果容器
    $('#scriptSegmentsContainer').show();
    
    // 触发自适应高度
    $('.auto-resize').each(function() {
        autoResizeTextarea(this);
    });
}

/**
 * 编辑片段
 */
function editSegment(index) {
    const textArea = $('#scriptSegmentsBody').find('tr').eq(index).find('.segment-text');
    textArea.focus();
}

/**
 * 上下移动片段
 */
function moveSegment(index, direction) {
    const tbody = $('#scriptSegmentsBody');
    const rows = tbody.find('tr');
    
    if (direction === 'up' && index > 0) {
        $(rows[index]).insertBefore($(rows[index - 1]));
        updateSegmentIndexes();
    } else if (direction === 'down' && index < rows.length - 1) {
        $(rows[index]).insertAfter($(rows[index + 1]));
        updateSegmentIndexes();
    }
}

/**
 * 删除片段
 */
function deleteSegment(index) {
    const tbody = $('#scriptSegmentsBody');
    const rows = tbody.find('tr');
    
    $(rows[index]).remove();
    updateSegmentIndexes();
    
    // 如果没有片段了，隐藏切分结果容器
    if (tbody.find('tr').length === 0) {
        $('#scriptSegmentsContainer').hide();
    }
}

/**
 * 更新片段序号和数据索引
 */
function updateSegmentIndexes() {
    const tbody = $('#scriptSegmentsBody');
    const rows = tbody.find('tr');
    
    rows.each(function(idx) {
        // 更新序号
        $(this).find('td:first').text(idx + 1);
        
        // 更新textArea的index
        $(this).find('.segment-text').data('index', idx);
    });
}

/**
 * 导入文案到剪映
 */
function importScriptToJianying() {
    const projectDir = $('#scriptProjectPath').val().trim();
    const projectName = $('#scriptProjectSelect').val();
    
    if (!projectDir || !projectName) {
        showError('scriptErrorArea', '请选择剪映项目');
        return;
    }
    
    // 获取字体大小
    let fontSize = parseFloat($('#fontSizeSelect').val());
    if ($('#fontSizeSelect').val() === 'custom') {
        fontSize = parseFloat($('#customFontSize').val());
    }
    
    // 验证字体大小
    if (isNaN(fontSize) || fontSize <= 0) {
        fontSize = 6.0; // 默认值
    }
    
    // 收集切分后的文本
    const segments = [];
    $('#scriptSegmentsBody').find('tr').each(function() {
        const text = $(this).find('.segment-text').val().trim();
        const durationText = $(this).find('.segment-duration').text();
        
        // 跳过空行
        if (text) {
            let duration = null;
            if (durationText !== '--') {
                // 将"秒"转换为微秒
                const seconds = parseFloat(durationText.replace('秒', ''));
                if (!isNaN(seconds)) {
                    duration = Math.round(seconds * 1000000); // 转换为微秒
                }
            }
            
            segments.push({
                text: text,
                duration: duration,
                font_size: fontSize
            });
        }
    });
    
    if (segments.length === 0) {
        showError('scriptErrorArea', '没有有效的文本段落');
        return;
    }
    
    $('#scriptLoadingArea').show();
    $('#scriptErrorArea').hide();
    $('#scriptSuccessArea').hide();
    
    $.ajax({
        url: '/import_script_to_jianying',
        type: 'POST',
        data: {
            project_dir: projectDir,
            project_name: projectName,
            segments: JSON.stringify(segments),
            font_size: fontSize
        },
        success: function(response) {
            $('#scriptLoadingArea').hide();
            if (response.success) {
                showSuccess('scriptSuccessArea', '文案已成功导入到剪映项目');
            } else {
                showError('scriptErrorArea', response.error || '导入文案失败');
            }
        },
        error: function(xhr) {
            $('#scriptLoadingArea').hide();
            const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : '服务器错误，请重试';
            showError('scriptErrorArea', errorMsg);
        }
    });
}

/**
 * 格式化时长显示
 */
function formatDuration(microseconds) {
    const seconds = microseconds / 1000000;
    return seconds.toFixed(1) + '秒';
}

/**
 * 显示成功信息
 */
function showSuccess(elementId, message) {
    $(`#${elementId}`).text(message).show();
    // 3秒后自动隐藏
    setTimeout(function() {
        $(`#${elementId}`).fadeOut();
    }, 3000);
}

/**
 * 显示错误信息
 */
function showError(elementId, message) {
    $(`#${elementId}`).text(message).show();
}

/**
 * 文本框自适应高度
 */
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// 绑定文本框自适应高度事件
$(document).on('input', '.auto-resize', function() {
    autoResizeTextarea(this);
}); 