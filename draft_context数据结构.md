# 文本

| 名称                     | 节点位置                                          | 备注                                                         |
| ------------------------ | ------------------------------------------------- | ------------------------------------------------------------ |
| 所有文本所在位置         | ["materials"]["texts"]                            |                                                              |
| 文本具体参数             | ["materials"]["texts"][0]["content"]              | ["materials"]["texts"][0]["content"]["styles"][0]["font"]["path"]  :字体样式，["materials"]["texts"][0]["content"]["styles"][0]["size"] :字体大小，["materials"]["texts"][0]["content"]["styles"][0]["fill"]["content"]["solid"]["color"]：字体颜色 |
| 文本ID                   | ["materials"]["texts"][0]["id"]                   | 后续可以根据这个ID和["tracks"][1]["segments"][0]["material_id"]相匹配，里面可以该字体颜色及坐标 |
| 字体显示坐标             | ["tracks"][1]["segments"][0]["clip"]["transform"] | 由x和y,x和y的区间范围[-1,1]                                  |
| 字体显示长度，及开始位置 | ["tracks"][1]["segments"][0]["target_timerange"]  | **duration**：字体长度，**start**：开始显示时间              |
| 选择角度                 | ["tracks"][1]["segments"][0]["clip"]["rotation"]  |                                                              |

### 音频部分

音频参数所在位置：["materials"]["audios"]

音频所在位置：["materials"]["audios"][0]["path"]，默认转换音频都会在draft_content.json目录下的textReading文件夹中

| 名称                 | 位置                                        | 备注                                                         |
| -------------------- | ------------------------------------------- | ------------------------------------------------------------ |
| 音频参数所在位置     | ["materials"]["audios"]                     |                                                              |
| 音频所在位置         | ["materials"]["audios"][0]["path"]          |                                                              |
| 文本转音频的文本ID   | ["materials"]["audios"][0]["text_id"]       | 后续可以根据这个text_id,可以根据ID替换音频，和["materials"]["audios"][0]["text_id"] |
| 音频ID               | ["materials"]["audios"][0]["id"]            | 后续可以根据ID在["tracks"][2]["segments"][0]["material_id"]中调整音频参数 |
| 音频的参数调整位置ID | ["tracks"][2]["segments"][0]["material_id"] | 音频显示长度：["tracks"][2]["segments"][0]["target_timerange"]["duration"]，音频开始显示位置：["tracks"][2]["segments"][0]["target_timerange"]["start"] |
| 调整参数类型         | ["tracks"][2]["type"]                       | **audio**，text，video                                       |
|                      |                                             |                                                              |

