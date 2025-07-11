$(document).ready(function() {
    // 初始化页面
    initPage();

    // 音频分类筛选功能 - 适用于所有带有category-badge的元素
    $(document).on('click', '.category-badge', function() {
        // 获取所在容器
        const container = $(this).closest('.card-body, .mb-3');
        
        // 移除当前容器内其他分类的active状态
        container.find('.category-badge').removeClass('active');
        
        // 添加当前分类的active状态
        $(this).addClass('active');
        
        // 获取选择的分类
        const selectedCategory = $(this).data('category');
        
        // 筛选表格行 - 查找当前容器下或整个文档中的表格行
        const rows = container.find('.voice-row').length > 0 
            ? container.find('.voice-row') 
            : $('.voice-row');
        
        if (selectedCategory === 'all') {
            rows.removeClass('filtered');
        } else {
            rows.each(function() {
                const rowCategory = $(this).data('category');
                if (rowCategory === selectedCategory) {
                    $(this).removeClass('filtered');
                } else {
                    $(this).addClass('filtered');
                }
            });
        }
    });
    
    // 分类下拉菜单变更事件
    $('.voice-category-select').on('change', function() {
        const voiceName = $(this).closest('tr').data('voice-name');
        const categoryId = $(this).val();
        
        // 显示加载指示器
        const row = $(this).closest('tr');
        const originalButtonHtml = row.find('.save-note-btn').html();
        row.find('.save-note-btn').prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>');
        
        // 发送更新分类请求
        $.ajax({
            url: '/update_voice_category',
            type: 'POST',
            data: {
                voice_name: voiceName,
                category_id: categoryId
            },
            success: function(response) {
                if (response.success) {
                    // 刷新页面以显示更新后的分类
                    location.reload();
                } else {
                    alert('更新分类失败');
                    // 恢复按钮状态
                    row.find('.save-note-btn').prop('disabled', false).html(originalButtonHtml);
                }
            },
            error: function() {
                alert('更新分类请求失败');
                // 恢复按钮状态
                row.find('.save-note-btn').prop('disabled', false).html(originalButtonHtml);
            }
        });
    });

    // 表格中音频选择
    $('input[name="voiceRadio"]').on('change', function() {
        const voicePath = $(this).closest('tr').data('voice-path');
        $('#selectedVoice').val(voicePath);
    });
    
    // 保存备注按钮点击事件
    $('.save-note-btn').on('click', function() {
        const row = $(this).closest('tr');
        const voiceName = row.data('voice-name');
        const note = row.find('.voice-note-input').val();
        
        // 发送保存备注请求
        $.ajax({
            url: '/update-note',
            type: 'POST',
            data: {
                voice_name: voiceName,
                note: note
            },
            success: function(response) {
                if (response.success) {
                    alert('备注已保存');
                } else {
                    alert('保存备注失败');
                }
            },
            error: function() {
                alert('保存备注请求失败');
            }
        });
    });

    // 模型选择变更不再需要重新加载语音列表，因为我们现在不按模型区分语音了

    // 文本生成提交表单
    $('#ttsForm').on('submit', function(e) {
        e.preventDefault();
        
        // 检查是否已选择音频
        if (!$('#selectedVoice').val()) {
            // 如果没有选择，自动选择第一个音频
            if ($('input[name="voiceRadio"]:checked').length > 0) {
                const voicePath = $('input[name="voiceRadio"]:checked').closest('tr').data('voice-path');
                $('#selectedVoice').val(voicePath);
            } else if ($('input[name="voiceRadio"]').length > 0) {
                const voicePath = $('input[name="voiceRadio"]').first().closest('tr').data('voice-path');
                $('#selectedVoice').val(voicePath);
                $('input[name="voiceRadio"]').first().prop('checked', true);
            } else {
                alert('请至少添加一个参考音频');
                return;
            }
        }
        
        // 显示加载状态
        $('#loadingArea').show();
        $('#resultArea').hide();
        $('#errorArea').hide();
        
        // 禁用按钮
        $('#generateBtn').prop('disabled', true);
        
        // 发送请求
        $.ajax({
            url: '/generate',
            type: 'POST',
            data: new FormData(this),
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    // 显示结果
                    $('#audioPlayer').attr('src', '/' + response.output_file);
                    $('#downloadLink').attr('href', '/' + response.output_file);
                    $('#generationTime').text('生成耗时: ' + response.generation_time + ' 秒');
                    $('#resultArea').show();
                } else {
                    // 显示错误
                    $('#errorArea').text(response.error).show();
                }
            },
            error: function(xhr) {
                // 显示错误
                let errorMsg = '生成失败';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                $('#errorArea').text(errorMsg).show();
            },
            complete: function() {
                // 隐藏加载状态
                $('#loadingArea').hide();
                // 启用按钮
                $('#generateBtn').prop('disabled', false);
            }
        });
    });

    // 高级设置参数实时更新显示
    $('#temperature').on('input', function() {
        $('#temperatureValue').text($(this).val());
    });
    
    $('#topP').on('input', function() {
        $('#topPValue').text($(this).val());
    });
    
    $('#topK').on('input', function() {
        $('#topKValue').text($(this).val());
    });
    
    $('#numBeams').on('input', function() {
        $('#numBeamsValue').text($(this).val());
    });
    
    $('#repetitionPenalty').on('input', function() {
        $('#repetitionPenaltyValue').text($(this).val());
    });
    
    $('#lengthPenalty').on('input', function() {
        $('#lengthPenaltyValue').text($(this).val());
    });
    
    $('#maxTextTokensPerSentence').on('input', function() {
        $('#maxTokensValue').text($(this).val());
    });
    
    $('#sentencesBucketMaxSize').on('input', function() {
        $('#bucketSizeValue').text($(this).val());
    });
    
    // 推理模式变更时显示/隐藏分句桶设置
    $('#inferMode').on('change', function() {
        if ($(this).val() === '批次推理') {
            $('#bucketSizeContainer').show();
        } else {
            $('#bucketSizeContainer').hide();
        }
    });
    
    // 历史记录相关事件处理
    
    // 播放记录音频
    $('.play-record-btn').on('click', function() {
        const outputFile = $(this).data('output-file');
        $('#historyPlayer').attr('src', '/' + outputFile);
        $('#historyPlayerArea').show();
        $('#historyPlayer')[0].play();
    });
    
    // 查看文本内容
    $('.view-text-btn').on('click', function() {
        const text = $(this).data('text');
        $('#modalTextContent').val(text);
        $('#textModal').modal('show');
        
        // 自动调整文本框高度
        autoResizeTextarea(document.getElementById('modalTextContent'));
    });
    
    // 删除记录
    $('.delete-record-btn').on('click', function() {
        if (confirm('确定要删除这条记录吗？')) {
            const recordId = $(this).closest('tr').data('record-id');
            
            $.ajax({
                url: '/delete_record',
                type: 'POST',
                data: {
                    record_id: recordId
                },
                success: function(response) {
                    if (response.success) {
                        // 刷新页面
                        location.reload();
                    } else {
                        alert('删除记录失败');
                    }
                },
                error: function() {
                    alert('删除请求失败');
                }
            });
        }
    });
    
    // 文本框自适应高度
    function autoResizeTextarea(textarea) {
        if (!textarea) return;
        
        textarea.style.height = 'auto';
        const maxHeight = 300; // 设置最大高度为300px
        
        // 如果内容高度超过最大高度，则启用滚动条
        if (textarea.scrollHeight > maxHeight) {
            textarea.style.height = maxHeight + 'px';
            textarea.style.overflowY = 'auto';
        } else {
            textarea.style.height = textarea.scrollHeight + 'px';
            textarea.style.overflowY = 'hidden';
        }
    }
    
    // 绑定文本框自适应高度事件
    $('.auto-resize').on('input', function() {
        autoResizeTextarea(this);
    });
    
    // 页面加载完成后，调整所有自适应文本框
    $('.auto-resize').each(function() {
        autoResizeTextarea(this);
    });

    // 页面初始化函数
    function initPage() {
        // 设置默认选择的音频
        if ($('input[name="voiceRadio"]:checked').length > 0) {
            const voicePath = $('input[name="voiceRadio"]:checked').closest('tr').data('voice-path');
            $('#selectedVoice').val(voicePath);
        }
        
        // 初始化批次推理设置容器显示状态
        if ($('#inferMode').val() === '批次推理') {
            $('#bucketSizeContainer').show();
        } else {
            $('#bucketSizeContainer').hide();
        }
        
        // 初始化绑定音频表格的事件
        bindVoiceEvents();
        bindJianyingVoiceEvents();
    }
}); 

// 音频文件管理
$(document).ready(function() {
    // 批量上传音频
    $('#batchUploadBtn').on('click', function() {
        const form = $('#batchUploadAudioForm')[0];
        const formData = new FormData(form);
        
        // 验证表单
        if (!$('#batchAudioFiles').val()) {
            alert('请选择要上传的音频文件');
            return;
        }
        
        // 获取选择的文件数量
        const fileCount = $('#batchAudioFiles')[0].files.length;
        
        // 显示上传状态
        $('#uploadProgressContainer').show();
        $('#uploadProgressBar').css('width', '10%');
        $('#uploadStatusText').text(`正在上传 ${fileCount} 个文件...`);
        
        // 禁用按钮
        $(this).prop('disabled', true);
        
        // 发送请求
        $.ajax({
            url: '/batch_upload_audio',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            xhr: function() {
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', function(evt) {
                    if (evt.lengthComputable) {
                        const percentComplete = Math.min(90, Math.round((evt.loaded / evt.total) * 100));
                        $('#uploadProgressBar').css('width', percentComplete + '%');
                        $('#uploadStatusText').text(`上传进度: ${percentComplete}%`);
                    }
                }, false);
                return xhr;
            },
            success: function(response) {
                if (response.success) {
                    // 更新进度条
                    $('#uploadProgressBar').css('width', '100%');
                    $('#uploadStatusText').text(response.message);
                    
                    // 显示详细结果
                    let resultDetails = '';
                    if (response.details && response.details.length > 0) {
                        const successCount = response.details.filter(item => item.success).length;
                        const failCount = response.details.length - successCount;
                        
                        if (failCount > 0) {
                            resultDetails = `\n\n失败的文件:\n`;
                            response.details.forEach(item => {
                                if (!item.success) {
                                    resultDetails += `- ${item.filename}: ${item.message}\n`;
                                }
                            });
                            
                            alert(`上传结果: 成功 ${successCount} 个, 失败 ${failCount} 个${resultDetails}`);
                        }
                    }
                    
                    // 重置表单
                    form.reset();
                    
                    // 延迟后刷新页面
                    setTimeout(function() {
                        location.reload();
                    }, 2000);
                } else {
                    $('#uploadProgressBar').css('width', '100%').removeClass('bg-primary').addClass('bg-danger');
                    $('#uploadStatusText').text('上传失败: ' + response.error);
                    
                    // 延迟后隐藏进度条
                    setTimeout(function() {
                        $('#uploadProgressContainer').hide();
                        $('#uploadProgressBar').css('width', '0%').removeClass('bg-danger').addClass('bg-primary');
                    }, 3000);
                }
            },
            error: function(xhr) {
                let errorMsg = '上传失败';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                
                $('#uploadProgressBar').css('width', '100%').removeClass('bg-primary').addClass('bg-danger');
                $('#uploadStatusText').text('上传失败: ' + errorMsg);
                
                // 延迟后隐藏进度条
                setTimeout(function() {
                    $('#uploadProgressContainer').hide();
                    $('#uploadProgressBar').css('width', '0%').removeClass('bg-danger').addClass('bg-primary');
                }, 3000);
            },
            complete: function() {
                // 启用按钮
                $('#batchUploadBtn').prop('disabled', false);
            }
        });
    });

    // 删除音频
    $('body').on('click', '.delete-audio-btn', function() {
        const voiceName = $(this).data('voice-name');
        // 解码显示名称，但保持原始编码值用于请求
        $('#deleteAudioName').text(decodeURIComponent(voiceName));
        $('#deleteAudioModal').data('voice-name', voiceName);
        
        // 记录用于调试
        console.log('准备删除音频:', voiceName);
        console.log('解码后文件名:', decodeURIComponent(voiceName));
        
        $('#deleteAudioModal').modal('show');
    });

    // 确认删除音频
    $('#confirmDeleteAudioBtn').on('click', function() {
        const voiceName = $('#deleteAudioModal').data('voice-name');
        
        // 禁用按钮
        $(this).prop('disabled', true);
        
        // 显示加载状态
        const originalText = $(this).text();
        $(this).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...');
        
        console.log('发送删除请求:', voiceName);
        
        // 发送删除请求
        $.ajax({
            url: '/delete_audio',
            type: 'POST',
            data: {
                filename: voiceName
            },
            success: function(response) {
                // 重新启用按钮
                $('#confirmDeleteAudioBtn').prop('disabled', false).text(originalText);
                
                if (response.success) {
                    console.log('删除成功:', response);
                    // 关闭模态框
                    $('#deleteAudioModal').modal('hide');
                    
                    // 移除对应的表格行
                    const selector = `tr[data-voice-name="${voiceName}"]`;
                    console.log('查找表格行:', selector);
                    const row = $(selector);
                    
                    if (row.length > 0) {
                        row.fadeOut(300, function() {
                            $(this).remove();
                        });
                    } else {
                        console.error('未找到对应的表格行:', voiceName);
                        // 尝试刷新页面
                        setTimeout(function() {
                            location.reload();
                        }, 1000);
                    }
                    
                    // 显示成功消息
                    alert('音频文件已删除');
                } else {
                    console.error('删除失败:', response);
                    alert('删除失败: ' + response.error);
                }
            },
            error: function(xhr, status, error) {
                // 重新启用按钮
                $('#confirmDeleteAudioBtn').prop('disabled', false).text(originalText);
                
                console.error('删除请求失败:', xhr.responseJSON || xhr.responseText);
                console.error('状态:', status);
                console.error('错误:', error);
                
                let errorMessage = '删除请求失败';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage += ': ' + xhr.responseJSON.error;
                } else if (xhr.responseText) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (response.error) {
                            errorMessage += ': ' + response.error;
                        }
                    } catch(e) {
                        errorMessage += ': ' + xhr.responseText;
                    }
                }
                
                alert(errorMessage);
            }
        });
    });
    
    // 添加音频分类
    $('#addCategoryBtn').on('click', function() {
        const categoryId = $('#categoryId').val();
        const categoryName = $('#categoryName').val();
        
        if (!categoryId || !categoryId.trim()) {
            alert('请输入分类ID');
            return;
        }
        
        if (!categoryName || !categoryName.trim()) {
            alert('请输入分类名称');
            return;
        }
        
        // 显示加载指示器
        const originalText = $(this).text();
        $(this).prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 添加中...');
        
        $.ajax({
            url: '/add_category',
            type: 'POST',
            data: {
                category_id: categoryId,
                category_name: categoryName
            },
            success: function(response) {
                if (response.success) {
                    // 刷新页面以更新分类列表
                    location.reload();
                } else {
                    alert('添加分类失败: ' + response.error);
                }
            },
            error: function(xhr) {
                const response = xhr.responseJSON || {};
                alert('添加分类失败: ' + (response.error || '服务器错误'));
            },
            complete: function() {
                // 恢复按钮状态
                $('#addCategoryBtn').prop('disabled', false).text(originalText);
            }
        });
    });
    
    // 删除分类
    $('.delete-category-btn').on('click', function() {
        const row = $(this).closest('tr');
        const categoryId = row.data('category-id');
        const categoryName = row.find('td:nth-child(2)').text();
        
        $('#deleteCategoryName').text(categoryName + ' (' + categoryId + ')');
        $('#confirmDeleteCategoryBtn').data('category-id', categoryId);
        $('#deleteCategoryModal').modal('show');
    });
    
    // 确认删除分类
    $('#confirmDeleteCategoryBtn').on('click', function() {
        const categoryId = $(this).data('category-id');
        
        // 显示加载指示器
        const originalText = $(this).text();
        $(this).prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...');
        
        $.ajax({
            url: '/delete_category',
            type: 'POST',
            data: { category_id: categoryId },
            success: function(response) {
                if (response.success) {
                    // 刷新页面以更新分类列表
                    location.reload();
                } else {
                    alert('删除分类失败: ' + response.error);
                }
            },
            error: function(xhr) {
                const response = xhr.responseJSON || {};
                alert('删除分类失败: ' + (response.error || '服务器错误'));
            },
            complete: function() {
                // 恢复按钮状态
                $('#confirmDeleteCategoryBtn').prop('disabled', false).text(originalText);
                
                // 关闭模态框
                $('#deleteCategoryModal').modal('hide');
            }
        });
    });
}); 

// 批量上传音频
$('#batchUploadBtn').on('click', function() {
    const form = $('#batchUploadAudioForm')[0];
    const formData = new FormData(form);
    
    // 验证表单
    if (!$('#batchAudioFiles').val()) {
        alert('请选择要上传的音频文件');
        return;
    }
    
    // 获取选择的文件数量
    const fileCount = $('#batchAudioFiles')[0].files.length;
    
    // 显示上传状态
    $('#uploadProgressContainer').show();
    $('#uploadProgressBar').css('width', '10%');
    $('#uploadStatusText').text(`正在上传 ${fileCount} 个文件...`);
    
    // 禁用按钮
    $(this).prop('disabled', true);
    
    // 发送请求
    $.ajax({
        url: '/batch_upload_audio',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            // 更新进度条
            $('#uploadProgressBar').css('width', '100%');
            $('#uploadStatusText').text(response.message);
            
            // 更新音频列表
            if (response.voices) {
                updateVoiceTable(response.voices);
            }
            
            // 清空文件输入
            $('#batchAudioFiles').val('');
            
            // 显示详细结果
            if (response.details && response.details.length > 0) {
                let detailsHtml = '<div class="mt-3"><h6>上传详情：</h6><ul class="list-group">';
                
                response.details.forEach(detail => {
                    if (detail.success) {
                        detailsHtml += `
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <span>${detail.filename}</span>
                                <span class="badge bg-success">成功</span>
                            </li>
                        `;
                    } else {
                        detailsHtml += `
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <span>${detail.filename}: ${detail.message}</span>
                                <span class="badge bg-danger">失败</span>
                            </li>
                        `;
                    }
                });
                
                detailsHtml += '</ul></div>';
                $('#uploadStatusText').after(detailsHtml);
            }
        },
        error: function(xhr) {
            // 显示错误信息
            $('#uploadProgressBar').css('width', '100%').removeClass('bg-primary').addClass('bg-danger');
            $('#uploadStatusText').text('上传失败: ' + (xhr.responseJSON?.error || '未知错误'));
        },
        complete: function() {
            // 重新启用按钮
            $('#batchUploadBtn').prop('disabled', false);
            
            // 3秒后隐藏进度条
            setTimeout(function() {
                $('#uploadProgressContainer').fadeOut();
            }, 3000);
        }
    });
});

// 绑定普通音频表格的事件
function bindVoiceEvents() {
    // 表格中音频选择
    $('#voiceTable input[name="voiceRadio"]').on('change', function() {
        const voicePath = $(this).closest('tr').data('voice-path');
        $('#selectedVoice').val(voicePath);
    });
    
    // 保存备注按钮点击事件
    $('#voiceTable .save-note-btn').on('click', function() {
        const row = $(this).closest('tr');
        const voiceName = row.data('voice-name');
        const note = row.find('.voice-note-input').val();
        
        // 发送保存备注请求
        $.ajax({
            url: '/update-note',
            type: 'POST',
            data: {
                voice_name: voiceName,
                note: note
            },
            success: function(response) {
                if (response.success) {
                    alert('备注已保存');
                } else {
                    alert('保存备注失败');
                }
            },
            error: function() {
                alert('保存备注请求失败');
            }
        });
    });
    
    // 分类下拉菜单变更事件
    $('#voiceTable .voice-category-select').on('change', function() {
        const voiceName = $(this).closest('tr').data('voice-name');
        const categoryId = $(this).val();
        
        // 显示加载指示器
        const row = $(this).closest('tr');
        const originalButtonHtml = row.find('.save-note-btn').html();
        row.find('.save-note-btn').prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>');
        
        // 发送更新分类请求
        $.ajax({
            url: '/update_voice_category',
            type: 'POST',
            data: {
                voice_name: voiceName,
                category_id: categoryId
            },
            success: function(response) {
                if (response.success) {
                    // 刷新页面以显示更新后的分类
                    location.reload();
                } else {
                    alert('更新分类失败');
                    // 恢复按钮状态
                    row.find('.save-note-btn').prop('disabled', false).html(originalButtonHtml);
                }
            },
            error: function() {
                alert('更新分类请求失败');
                // 恢复按钮状态
                row.find('.save-note-btn').prop('disabled', false).html(originalButtonHtml);
            }
        });
    });
}

// 绑定剪映音频表格的事件
function bindJianyingVoiceEvents() {
    // 表格中音频选择
    $('#jianyingVoiceTable input[name="jianyingVoiceRadio"]').on('change', function() {
        const voicePath = $(this).closest('tr').data('voice-path');
        $('#jianyingSelectedVoice').val(voicePath);
    });
    
    // 保存备注按钮点击事件
    $('#jianyingVoiceTable .save-note-btn').on('click', function() {
        const row = $(this).closest('tr');
        const voiceName = row.data('voice-name');
        const note = row.find('.voice-note-input').val();
        
        // 发送保存备注请求
        $.ajax({
            url: '/update-note',
            type: 'POST',
            data: {
                voice_name: voiceName,
                note: note
            },
            success: function(response) {
                if (response.success) {
                    alert('备注已保存');
                } else {
                    alert('保存备注失败');
                }
            },
            error: function() {
                alert('保存备注请求失败');
            }
        });
    });
    
    // 分类下拉菜单变更事件
    $('#jianyingVoiceTable .voice-category-select').on('change', function() {
        const voiceName = $(this).closest('tr').data('voice-name');
        const categoryId = $(this).val();
        
        // 显示加载指示器
        const row = $(this).closest('tr');
        const originalButtonHtml = row.find('.save-note-btn').html();
        row.find('.save-note-btn').prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>');
        
        // 发送更新分类请求
        $.ajax({
            url: '/update_voice_category',
            type: 'POST',
            data: {
                voice_name: voiceName,
                category_id: categoryId
            },
            success: function(response) {
                if (response.success) {
                    // 刷新页面以显示更新后的分类
                    location.reload();
                } else {
                    alert('更新分类失败');
                    // 恢复按钮状态
                    row.find('.save-note-btn').prop('disabled', false).html(originalButtonHtml);
                }
            },
            error: function() {
                alert('更新分类请求失败');
                // 恢复按钮状态
                row.find('.save-note-btn').prop('disabled', false).html(originalButtonHtml);
            }
        });
    });
}

// 更新音频表格
function updateVoiceTable(voices) {
    const tables = ['#voiceTable', '#jianyingVoiceTable', '#audioManageTable'];
    
    tables.forEach(tableId => {
        const table = $(tableId);
        if (table.length === 0) return;
        
        const tbody = table.find('tbody');
        tbody.empty();
        
        voices.forEach((voice, index) => {
            const isRadioTable = tableId === '#voiceTable' || tableId === '#jianyingVoiceTable';
            
            let row = `<tr data-voice-path="${voice.path}" data-voice-name="${encodeURIComponent(voice.name)}" data-category="${voice.category}" class="voice-row">`;
            
            // 添加单选按钮列（仅对特定表格）
            if (isRadioTable) {
                row += `<td><input type="radio" name="${tableId === '#voiceTable' ? 'voiceRadio' : 'jianyingVoiceRadio'}" class="form-check-input" ${index === 0 ? 'checked' : ''}></td>`;
            }
            
            // 添加其他列
            row += `
                <td>${voice.name}</td>
                <td>
                    <audio src="/audio/${voice.path}" controls class="audio-player w-100"></audio>
                </td>
                <td>
                    <input type="text" class="form-control voice-note-input" value="${voice.note}" placeholder="添加备注">
                </td>
                <td>
                    <select class="form-select form-select-sm voice-category-select">
            `;
            
            // 添加分类选项
            $('.category-badge').each(function() {
                const categoryId = $(this).data('category');
                if (categoryId !== 'all') {
                    const categoryName = $(this).text();
                    row += `<option value="${categoryId}" ${voice.category === categoryId ? 'selected' : ''}>${categoryName}</option>`;
                }
            });
            
            row += `
                    </select>
                </td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-sm btn-outline-primary save-note-btn">保存</button>
                        <button type="button" class="btn btn-sm btn-outline-danger delete-audio-btn" data-voice-name="${encodeURIComponent(voice.name)}">删除</button>
                    </div>
                </td>
            </tr>`;
            
            tbody.append(row);
        });
        
        // 重新绑定事件
        if (tableId === '#voiceTable') {
            bindVoiceEvents();
        } else if (tableId === '#jianyingVoiceTable') {
            bindJianyingVoiceEvents();
        }
    });
} 