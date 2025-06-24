$(document).ready(function() {
    // 初始化字体选择器
    let availableFonts = [];
    
    // 加载可用字体
    function loadAvailableFonts() {
        $.get('/get_available_fonts', function(response) {
            if (response.success) {
                availableFonts = response.fonts;
            } else {
                showFontError('加载字体列表失败：' + response.error);
            }
        });
    }
    
    // 显示错误信息
    function showFontError(message) {
        $('#fontErrorArea').text(message).show();
        setTimeout(() => {
            $('#fontErrorArea').fadeOut();
        }, 5000);
    }
    
    // 显示成功信息
    function showFontSuccess(message) {
        $('#fontSuccessArea').text(message).show();
        setTimeout(() => {
            $('#fontSuccessArea').fadeOut();
        }, 5000);
    }
    
    // 检查项目目录
    $('#fontCheckProjectBtn').click(function() {
        const projectDir = $('#fontProjectPath').val();
        if (!projectDir) {
            showFontError('请输入项目目录路径');
            return;
        }
        
        $('#fontLoadingArea').show();
        $.post('/check_jianying_project', {
            project_dir: projectDir
        }, function(response) {
            $('#fontLoadingArea').hide();
            if (response.success) {
                $('#fontProjectSelectContainer').show();
                // 加载项目列表
                const select = $('#fontProjectSelect');
                select.empty();
                response.projects.forEach(project => {
                    select.append(`<option value="${project}">${project}</option>`);
                });
            } else {
                showFontError(response.error);
            }
        });
    });
    
    // 加载项目文本
    $('#loadFontProjectBtn').click(function() {
        const projectDir = $('#fontProjectPath').val();
        const projectName = $('#fontProjectSelect').val();
        
        if (!projectDir || !projectName) {
            showFontError('请选择项目目录和工程');
            return;
        }
        
        $('#fontLoadingArea').show();
        $.post('/load_jianying_text', {
            project_dir: projectDir,
            project_name: projectName
        }, function(response) {
            $('#fontLoadingArea').hide();
            if (response.success) {
                displayProjectTexts(response.texts);
                $('#projectTextList').show();
                $('#replaceFontBtn').show();
                $('#exportSubtitlesBtn').show();
            } else {
                showFontError(response.error);
            }
        });
    });
    
    // 导出字幕为TXT
    $('#exportSubtitlesBtn').click(function() {
        const projectDir = $('#fontProjectPath').val();
        const projectName = $('#fontProjectSelect').val();
        
        if (!projectDir || !projectName) {
            showFontError('请选择项目目录和工程');
            return;
        }
        
        $('#fontLoadingArea').show();
        $.post('/export_jianying_subtitles', {
            project_dir: projectDir,
            project_name: projectName
        }, function(response) {
            $('#fontLoadingArea').hide();
            if (response.success) {
                // 创建一个blob对象
                const blob = new Blob([response.subtitles_text], {type: 'text/plain;charset=utf-8'});
                
                // 创建下载链接
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `${projectName}_字幕.txt`;
                
                // 触发下载
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                showFontSuccess('字幕导出成功');
            } else {
                showFontError(response.error);
            }
        });
    });
    
    // 动态注册字体
    function registerFont(fontName, fontPath) {
        if (document.getElementById('font-style-' + fontName)) return; // 已注册
        const style = document.createElement('style');
        style.id = 'font-style-' + fontName;
        style.innerHTML = `
            @font-face {
                font-family: '${fontName}';
                src: url('/font/${fontPath.split(/[\\/]/).pop()}');
            }
        `;
        document.head.appendChild(style);
    }

    // 只渲染一次统一设置字体下拉框和按钮
    function ensureBatchFontUI() {
        if ($('#fontBatchSetContainer').length === 0) {
            $('#projectTextList').prepend(`
                <div class="mb-2" id="fontBatchSetContainer">
                    <label class="form-label me-2">统一设置字体：</label>
                    <select id="batchFontSelect" class="form-select d-inline-block" style="width:200px;"></select>
                    <button type="button" class="btn btn-sm btn-outline-primary ms-2" id="batchSetFontBtn">一键应用到所有下拉框</button>
                </div>
            `);
        }
    }

    function displayProjectTexts(texts) {
        ensureBatchFontUI();
        const tbody = $('#textListBody');
        tbody.empty();
        // 只移除一次"操作"表头
        if (!$('#textListTable thead tr').data('op-removed')) {
            $('#textListTable thead tr th:last-child').remove();
            $('#textListTable thead tr').data('op-removed', true);
        }
        
        texts.forEach((text, index) => {
            let realText = '';
            try {
                realText = JSON.parse(text.content).text || '';
            } catch(e) {
                realText = text.content;
            }
            // 取当前字体文件名作为 font-family
            const fontFileName = text.current_font ? text.current_font.split(/[\\/]/).pop().replace('.ttf','').replace('.otf','') : 'default';
            if (text.current_font) registerFont(fontFileName, text.current_font);

            const row = $('<tr>');
            row.append(`<td><input type="checkbox" class="form-check-input text-checkbox" data-text-id="${text.id}"></td>`);
            row.append(`<td>${realText}</td>`);
            row.append(`<td><div class="font-preview" style="font-family: '${fontFileName}';">${realText}</div></td>`);
            
            // 字体选择下拉框
            const fontSelect = $('<select>').addClass('form-select font-select');
            availableFonts.forEach(font => {
                fontSelect.append(`<option value="${font.path}" ${font.path === text.current_font ? 'selected' : ''}>${font.name}</option>`);
            });
            // 自动预览：绑定change事件
            fontSelect.on('change', function() {
                const selectedFontPath = $(this).val();
                const fontFileName = selectedFontPath.split(/[\\/]/).pop().replace('.ttf','').replace('.otf','');
                registerFont(fontFileName, selectedFontPath);
                $(this).closest('tr').find('.font-preview').css('font-family', fontFileName);
            });
            row.append($('<td>').append(fontSelect));
            // 移除操作列
            row.append($('<td style="display:none"></td>'));
            tbody.append(row);
        });

        // 填充统一设置下拉框
        const select = $('#batchFontSelect');
        select.empty();
        availableFonts.forEach(font => {
            select.append(`<option value="${font.path}">${font.name}</option>`);
        });

        // 重新绑定一键应用事件
        $('#batchSetFontBtn').off('click').on('click', function() {
            const fontPath = $('#batchFontSelect').val();
            const fontFileName = fontPath.split(/[\\/]/).pop().replace('.ttf','').replace('.otf','');
            registerFont(fontFileName, fontPath);
            $('.font-select').each(function() {
                $(this).val(fontPath).trigger('change');
            });
        });
    }
    
    // 全选/取消全选
    $('#selectAllTexts').change(function() {
        $('.text-checkbox').prop('checked', $(this).prop('checked'));
    });
    
    // 提交字体更换
    $('#jianyingFontForm').submit(function(e) {
        e.preventDefault();
        
        const projectDir = $('#fontProjectPath').val();
        const projectName = $('#fontProjectSelect').val();
        const selectedTexts = [];
        
        $('.text-checkbox:checked').each(function() {
            const textId = $(this).data('text-id');
            const fontPath = $(this).closest('tr').find('.font-select').val();
            selectedTexts.push({
                text_id: textId,
                font_path: fontPath
            });
        });
        
        if (selectedTexts.length === 0) {
            showFontError('请选择要更换字体的文本');
            return;
        }
        
        $('#fontLoadingArea').show();
        $.post('/replace_jianying_font', {
            project_dir: projectDir,
            project_name: projectName,
            text_replacements: JSON.stringify(selectedTexts)
        }, function(response) {
            $('#fontLoadingArea').hide();
            if (response.success) {
                showFontSuccess('字体更换成功');
                // 重新加载文本列表
                $('#loadFontProjectBtn').click();
            } else {
                showFontError(response.error);
            }
        });
    });
    
    // 初始化
    loadAvailableFonts();
}); 