$(document).ready(function() {
    // 全局变量
    let selectedModel = $('#modelSelect').val();
    let selectedVoice = '';

    // 初始化时设置第一个选中的音频
    const firstVoiceRow = $('#voiceTable tbody tr:first');
    if (firstVoiceRow.length > 0) {
        selectedVoice = firstVoiceRow.data('voice-path');
        $('#selectedVoice').val(selectedVoice);
    }

    // 模型选择改变时，加载对应的参考音频列表
    $('#modelSelect').on('change', function() {
        selectedModel = $(this).val();
        loadVoices(selectedModel);
    });

    // 音频行选择
    $('#voiceTable').on('click', 'tr', function() {
        $('#voiceTable tr').removeClass('table-active');
        $(this).addClass('table-active');
        $(this).find('input[type="radio"]').prop('checked', true);
        
        selectedVoice = $(this).data('voice-path');
        $('#selectedVoice').val(selectedVoice);
    });

    // 保存备注按钮点击
    $('.save-note-btn').on('click', function() {
        const row = $(this).closest('tr');
        const modelPath = selectedModel;
        const voiceName = row.data('voice-name');
        const note = row.find('.voice-note-input').val();
        
        saveVoiceNote(modelPath, voiceName, note);
    });

    // 提交表单
    $('#ttsForm').on('submit', function(e) {
        e.preventDefault();
        
        const text = $('#textInput').val().trim();
        if (!text) {
            showError('请输入要转换的文本');
            return;
        }
        
        if (!selectedVoice) {
            showError('请选择参考音频');
            return;
        }
        
        // 显示加载动画
        $('#loadingArea').show();
        $('#resultArea').hide();
        $('#errorArea').hide();
        
        // 获取表单数据，包括高级参数
        const formData = new FormData(this);
        
        // 处理复选框
        formData.set('do_sample', $('#doSample').is(':checked') ? 'true' : 'false');
        
        // 发送请求
        $.ajax({
            url: '/generate',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('#loadingArea').hide();
                
                if (response.success) {
                    $('#resultArea').show();
                    $('#audioPlayer').attr('src', '/' + response.output_file);
                    $('#downloadLink').attr('href', '/' + response.output_file);
                    $('#generationTime').text('生成耗时: ' + response.generation_time + ' 秒');
                    
                    // 更新历史记录表格
                    updateHistoryTable(response.record);
                } else {
                    showError(response.error || '生成失败');
                }
            },
            error: function(xhr) {
                $('#loadingArea').hide();
                try {
                    const response = JSON.parse(xhr.responseText);
                    showError(response.error || '生成请求失败');
                } catch (e) {
                    showError('服务器错误');
                }
            }
        });
    });

    // 播放历史记录音频
    $('#historyTable').on('click', '.play-record-btn', function() {
        const outputFile = $(this).data('output-file');
        $('#historyPlayer').attr('src', '/' + outputFile);
        $('#historyPlayerArea').show();
        
        // 播放音频
        $('#historyPlayer')[0].play();
    });

    // 查看文本按钮点击
    $('#historyTable').on('click', '.view-text-btn', function() {
        const text = $(this).data('text');
        $('#modalTextContent').val(text);
        
        // 显示模态框
        var myModal = new bootstrap.Modal(document.getElementById('textModal'));
        myModal.show();
    });

    // 删除记录按钮点击
    $('#historyTable').on('click', '.delete-record-btn', function() {
        if (!confirm('确定要删除此记录吗？')) {
            return;
        }
        
        const row = $(this).closest('tr');
        const recordId = row.data('record-id');
        
        $.ajax({
            url: '/delete_record',
            type: 'POST',
            data: {
                record_id: recordId
            },
            success: function(response) {
                if (response.success) {
                    row.remove();
                    
                    // 更新记录数量
                    const count = $('#historyTable tbody tr').length;
                    $('#recordCount').text('共 ' + count + ' 条记录');
                    
                    // 如果没有记录了，显示提示
                    if (count === 0) {
                        $('#historyTable tbody').html('<tr><td colspan="6" class="text-center">暂无生成记录</td></tr>');
                    }
                }
            }
        });
    });

    // 加载音频列表
    function loadVoices(modelPath) {
        $.get('/get_voices', { model_path: modelPath }, function(voices) {
            // 清空表格
            $('#voiceTable tbody').empty();
            
            // 填充表格
            voices.forEach(function(voice, index) {
                const row = $('<tr>').attr({
                    'data-voice-path': voice.path,
                    'data-voice-name': voice.name
                });
                
                row.append($('<td>').append(
                    $('<input>').attr({
                        type: 'radio',
                        name: 'voiceRadio',
                        class: 'form-check-input',
                        checked: index === 0
                    })
                ));
                
                row.append($('<td>').text(voice.name));
                row.append($('<td>').append(
                    $('<audio>').attr({
                        src: '/audio/' + voice.path,
                        controls: true,
                        class: 'audio-player w-100'
                    })
                ));
                row.append($('<td>').append(
                    $('<input>').attr({
                        type: 'text',
                        class: 'form-control voice-note-input',
                        value: voice.note,
                        placeholder: '添加备注'
                    })
                ));
                row.append($('<td>').append(
                    $('<button>').attr({
                        type: 'button',
                        class: 'btn btn-sm btn-outline-primary save-note-btn'
                    }).text('保存备注')
                ));
                
                $('#voiceTable tbody').append(row);
            });
            
            // 如果有音频，设置第一个为选中状态
            const firstVoiceRow = $('#voiceTable tbody tr:first');
            if (firstVoiceRow.length > 0) {
                selectedVoice = firstVoiceRow.data('voice-path');
                $('#selectedVoice').val(selectedVoice);
            } else {
                selectedVoice = '';
                $('#selectedVoice').val('');
            }
        });
    }

    // 保存音频备注
    function saveVoiceNote(modelPath, voiceName, note) {
        $.ajax({
            url: '/update-note',
            type: 'POST',
            data: {
                model_path: modelPath,
                voice_name: voiceName,
                note: note
            },
            success: function(response) {
                if (response.success) {
                    alert('备注保存成功！');
                }
            },
            error: function() {
                alert('备注保存失败！');
            }
        });
    }

    // 更新历史表格
    function updateHistoryTable(record) {
        // 创建一个新的行
        const row = $('<tr>').attr('data-record-id', record.id);
        
        row.append($('<td>').text(record.timestamp));
        row.append($('<td>').text(record.model));
        row.append($('<td>').text(record.voice));
        row.append($('<td>').text(record.generation_time + ' 秒'));
        
        const textCell = $('<td>').addClass('text-truncate').attr('title', record.full_text).text(record.text);
        row.append(textCell);
        
        const actionCell = $('<td>');
        const btnGroup = $('<div>').addClass('btn-group btn-group-sm flex-wrap').attr('role', 'group');
        
        // 添加按钮
        btnGroup.append(
            $('<button>').attr({
                type: 'button',
                class: 'btn btn-sm btn-outline-primary play-record-btn',
                'data-output-file': record.output_file
            }).text('播放')
        );
        
        btnGroup.append(
            $('<a>').attr({
                href: '/' + record.output_file,
                download: '',
                class: 'btn btn-sm btn-outline-success'
            }).text('下载')
        );
        
        btnGroup.append(
            $('<button>').attr({
                type: 'button',
                class: 'btn btn-sm btn-outline-info view-text-btn',
                'data-text': record.full_text
            }).text('查看文本')
        );
        
        btnGroup.append(
            $('<button>').attr({
                type: 'button',
                class: 'btn btn-sm btn-outline-danger delete-record-btn'
            }).text('删除')
        );
        
        actionCell.append(btnGroup);
        row.append(actionCell);
        
        // 添加到表格的顶部
        $('#historyTable tbody').prepend(row);
        
        // 更新记录数量
        const count = $('#historyTable tbody tr').length;
        $('#recordCount').text('共 ' + count + ' 条记录');
        
        // 如果表格之前是空的，移除"暂无记录"行
        $('#historyTable tbody tr td[colspan="6"]').parent().remove();
    }

    // 显示错误消息
    function showError(message) {
        $('#errorArea').show().text(message);
    }

    // 自动调整文本框高度
    $('.auto-resize').on('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // 初始调整所有auto-resize文本框
    $('.auto-resize').each(function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
}); 