FFmpeg 64-bit static Windows build from www.gyan.dev

Version: 2025-05-15-git-12b853530a-essentials_build-www.gyan.dev

License: GPL v3

Source Code: https://github.com/FFmpeg/FFmpeg/commit/12b853530a

git-essentials build configuration: 

ARCH                      x86 (generic)
big-endian                no
runtime cpu detection     yes
standalone assembly       yes
x86 assembler             nasm
MMX enabled               yes
MMXEXT enabled            yes
3DNow! enabled            yes
3DNow! extended enabled   yes
SSE enabled               yes
SSSE3 enabled             yes
AESNI enabled             yes
AVX enabled               yes
AVX2 enabled              yes
AVX-512 enabled           yes
AVX-512ICL enabled        yes
XOP enabled               yes
FMA3 enabled              yes
FMA4 enabled              yes
i686 features enabled     yes
CMOV is fast              yes
EBX available             yes
EBP available             yes
debug symbols             yes
strip symbols             yes
optimize for size         no
optimizations             yes
static                    yes
shared                    no
network support           yes
threading support         pthreads
safe bitstream reader     yes
texi2html enabled         no
perl enabled              yes
pod2man enabled           yes
makeinfo enabled          yes
makeinfo supports HTML    yes
xmllint enabled           yes

External libraries:
avisynth                libopencore_amrnb       libvpx
bzlib                   libopencore_amrwb       libwebp
gmp                     libopenjpeg             libx264
gnutls                  libopenmpt              libx265
iconv                   libopus                 libxml2
libaom                  librubberband           libxvid
libass                  libspeex                libzimg
libfontconfig           libsrt                  libzmq
libfreetype             libssh                  lzma
libfribidi              libtheora               mediafoundation
libgme                  libvidstab              sdl2
libgsm                  libvmaf                 zlib
libharfbuzz             libvo_amrwbenc
libmp3lame              libvorbis

External libraries providing hardware acceleration:
amf                     d3d12va                 nvdec
cuda                    dxva2                   nvenc
cuda_llvm               ffnvcodec               vaapi
cuvid                   libmfx
d3d11va                 libvpl

Libraries:
avcodec                 avformat                swscale
avdevice                avutil
avfilter                swresample

Programs:
ffmpeg                  ffplay                  ffprobe

Enabled decoders:
aac                     fourxm                  pfm
aac_fixed               fraps                   pgm
aac_latm                frwu                    pgmyuv
aasc                    ftr                     pgssub
ac3                     g2m                     pgx
ac3_fixed               g723_1                  phm
acelp_kelvin            g729                    photocd
adpcm_4xm               gdv                     pictor
adpcm_adx               gem                     pixlet
adpcm_afc               gif                     pjs
adpcm_agm               gremlin_dpcm            png
adpcm_aica              gsm                     ppm
adpcm_argo              gsm_ms                  prores
adpcm_ct                h261                    prosumer
adpcm_dtk               h263                    psd
adpcm_ea                h263i                   ptx
adpcm_ea_maxis_xa       h263p                   qcelp
adpcm_ea_r1             h264                    qdm2
adpcm_ea_r2             h264_amf                qdmc
adpcm_ea_r3             h264_cuvid              qdraw
adpcm_ea_xas            h264_qsv                qoa
adpcm_g722              hap                     qoi
adpcm_g726              hca                     qpeg
adpcm_g726le            hcom                    qtrle
adpcm_ima_acorn         hdr                     r10k
adpcm_ima_alp           hevc                    r210
adpcm_ima_amv           hevc_amf                ra_144
adpcm_ima_apc           hevc_cuvid              ra_288
adpcm_ima_apm           hevc_qsv                ralf
adpcm_ima_cunning       hnm4_video              rasc
adpcm_ima_dat4          hq_hqa                  rawvideo
adpcm_ima_dk3           hqx                     realtext
adpcm_ima_dk4           huffyuv                 rka
adpcm_ima_ea_eacs       hymt                    rl2
adpcm_ima_ea_sead       iac                     roq
adpcm_ima_iss           idcin                   roq_dpcm
adpcm_ima_moflex        idf                     rpza
adpcm_ima_mtf           iff_ilbm                rscc
adpcm_ima_oki           ilbc                    rtv1
adpcm_ima_qt            imc                     rv10
adpcm_ima_rad           imm4                    rv20
adpcm_ima_smjpeg        imm5                    rv30
adpcm_ima_ssi           indeo2                  rv40
adpcm_ima_wav           indeo3                  rv60
adpcm_ima_ws            indeo4                  s302m
adpcm_ima_xbox          indeo5                  sami
adpcm_ms                interplay_acm           sanm
adpcm_mtaf              interplay_dpcm          sbc
adpcm_psx               interplay_video         scpr
adpcm_sbpro_2           ipu                     screenpresso
adpcm_sbpro_3           jacosub                 sdx2_dpcm
adpcm_sbpro_4           jpeg2000                sga
adpcm_swf               jpegls                  sgi
adpcm_thp               jv                      sgirle
adpcm_thp_le            kgv1                    sheervideo
adpcm_vima              kmvc                    shorten
adpcm_xa                lagarith                simbiosis_imx
adpcm_xmd               lead                    sipr
adpcm_yamaha            libaom_av1              siren
adpcm_zork              libgsm                  smackaud
agm                     libgsm_ms               smacker
aic                     libopencore_amrnb       smc
alac                    libopencore_amrwb       smvjpeg
alias_pix               libopus                 snow
als                     libspeex                sol_dpcm
amrnb                   libvorbis               sonic
amrwb                   libvpx_vp8              sp5x
amv                     libvpx_vp9              speedhq
anm                     loco                    speex
ansi                    lscr                    srgc
anull                   m101                    srt
apac                    mace3                   ssa
ape                     mace6                   stl
apng                    magicyuv                subrip
aptx                    mdec                    subviewer
aptx_hd                 media100                subviewer1
apv                     metasound               sunrast
arbc                    microdvd                svq1
argo                    mimic                   svq3
ass                     misc4                   tak
asv1                    mjpeg                   targa
asv2                    mjpeg_cuvid             targa_y216
atrac1                  mjpeg_qsv               tdsc
atrac3                  mjpegb                  text
atrac3al                mlp                     theora
atrac3p                 mmvideo                 thp
atrac3pal               mobiclip                tiertexseqvideo
atrac9                  motionpixels            tiff
aura                    movtext                 tmv
aura2                   mp1                     truehd
av1                     mp1float                truemotion1
av1_amf                 mp2                     truemotion2
av1_cuvid               mp2float                truemotion2rt
av1_qsv                 mp3                     truespeech
avrn                    mp3adu                  tscc
avrp                    mp3adufloat             tscc2
avs                     mp3float                tta
avui                    mp3on4                  twinvq
bethsoftvid             mp3on4float             txd
bfi                     mpc7                    ulti
bink                    mpc8                    utvideo
binkaudio_dct           mpeg1_cuvid             v210
binkaudio_rdft          mpeg1video              v210x
bintext                 mpeg2_cuvid             v308
bitpacked               mpeg2_qsv               v408
bmp                     mpeg2video              v410
bmv_audio               mpeg4                   vb
bmv_video               mpeg4_cuvid             vble
bonk                    mpegvideo               vbn
brender_pix             mpl2                    vc1
c93                     msa1                    vc1_cuvid
cavs                    mscc                    vc1_qsv
cbd2_dpcm               msmpeg4v1               vc1image
ccaption                msmpeg4v2               vcr1
cdgraphics              msmpeg4v3               vmdaudio
cdtoons                 msnsiren                vmdvideo
cdxl                    msp2                    vmix
cfhd                    msrle                   vmnc
cinepak                 mss1                    vnull
clearvideo              mss2                    vorbis
cljr                    msvideo1                vp3
cllc                    mszh                    vp4
comfortnoise            mts2                    vp5
cook                    mv30                    vp6
cpia                    mvc1                    vp6a
cri                     mvc2                    vp6f
cscd                    mvdv                    vp7
cyuv                    mvha                    vp8
dca                     mwsc                    vp8_cuvid
dds                     mxpeg                   vp8_qsv
derf_dpcm               nellymoser              vp9
dfa                     notchlc                 vp9_cuvid
dfpwm                   nuv                     vp9_qsv
dirac                   on2avc                  vplayer
dnxhd                   opus                    vqa
dolby_e                 osq                     vqc
dpx                     paf_audio               vvc
dsd_lsbf                paf_video               vvc_qsv
dsd_lsbf_planar         pam                     wady_dpcm
dsd_msbf                pbm                     wavarc
dsd_msbf_planar         pcm_alaw                wavpack
dsicinaudio             pcm_bluray              wbmp
dsicinvideo             pcm_dvd                 wcmv
dss_sp                  pcm_f16le               webp
dst                     pcm_f24le               webvtt
dvaudio                 pcm_f32be               wmalossless
dvbsub                  pcm_f32le               wmapro
dvdsub                  pcm_f64be               wmav1
dvvideo                 pcm_f64le               wmav2
dxa                     pcm_lxf                 wmavoice
dxtory                  pcm_mulaw               wmv1
dxv                     pcm_s16be               wmv2
eac3                    pcm_s16be_planar        wmv3
eacmv                   pcm_s16le               wmv3image
eamad                   pcm_s16le_planar        wnv1
eatgq                   pcm_s24be               wrapped_avframe
eatgv                   pcm_s24daud             ws_snd1
eatqi                   pcm_s24le               xan_dpcm
eightbps                pcm_s24le_planar        xan_wc3
eightsvx_exp            pcm_s32be               xan_wc4
eightsvx_fib            pcm_s32le               xbin
escape124               pcm_s32le_planar        xbm
escape130               pcm_s64be               xface
evrc                    pcm_s64le               xl
exr                     pcm_s8                  xma1
fastaudio               pcm_s8_planar           xma2
ffv1                    pcm_sga                 xpm
ffvhuff                 pcm_u16be               xsub
ffwavesynth             pcm_u16le               xwd
fic                     pcm_u24be               y41p
fits                    pcm_u24le               ylc
flac                    pcm_u32be               yop
flashsv                 pcm_u32le               yuv4
flashsv2                pcm_u8                  zero12v
flic                    pcm_vidc                zerocodec
flv                     pcx                     zlib
fmvc                    pdv                     zmbv

Enabled encoders:
a64multi                hevc_d3d12va            pcm_u16le
a64multi5               hevc_mf                 pcm_u24be
aac                     hevc_nvenc              pcm_u24le
aac_mf                  hevc_qsv                pcm_u32be
ac3                     hevc_vaapi              pcm_u32le
ac3_fixed               huffyuv                 pcm_u8
ac3_mf                  jpeg2000                pcm_vidc
adpcm_adx               jpegls                  pcx
adpcm_argo              libaom_av1              pfm
adpcm_g722              libgsm                  pgm
adpcm_g726              libgsm_ms               pgmyuv
adpcm_g726le            libmp3lame              phm
adpcm_ima_alp           libopencore_amrnb       png
adpcm_ima_amv           libopenjpeg             ppm
adpcm_ima_apm           libopus                 prores
adpcm_ima_qt            libspeex                prores_aw
adpcm_ima_ssi           libtheora               prores_ks
adpcm_ima_wav           libvo_amrwbenc          qoi
adpcm_ima_ws            libvorbis               qtrle
adpcm_ms                libvpx_vp8              r10k
adpcm_swf               libvpx_vp9              r210
adpcm_yamaha            libwebp                 ra_144
alac                    libwebp_anim            rawvideo
alias_pix               libx264                 roq
amv                     libx264rgb              roq_dpcm
anull                   libx265                 rpza
apng                    libxvid                 rv10
aptx                    ljpeg                   rv20
aptx_hd                 magicyuv                s302m
ass                     mjpeg                   sbc
asv1                    mjpeg_qsv               sgi
asv2                    mjpeg_vaapi             smc
av1_amf                 mlp                     snow
av1_mf                  movtext                 speedhq
av1_nvenc               mp2                     srt
av1_qsv                 mp2fixed                ssa
av1_vaapi               mp3_mf                  subrip
avrp                    mpeg1video              sunrast
avui                    mpeg2_qsv               svq1
bitpacked               mpeg2_vaapi             targa
bmp                     mpeg2video              text
cfhd                    mpeg4                   tiff
cinepak                 msmpeg4v2               truehd
cljr                    msmpeg4v3               tta
comfortnoise            msrle                   ttml
dca                     msvideo1                utvideo
dfpwm                   nellymoser              v210
dnxhd                   opus                    v308
dpx                     pam                     v408
dvbsub                  pbm                     v410
dvdsub                  pcm_alaw                vbn
dvvideo                 pcm_bluray              vc2
dxv                     pcm_dvd                 vnull
eac3                    pcm_f32be               vorbis
exr                     pcm_f32le               vp8_vaapi
ffv1                    pcm_f64be               vp9_qsv
ffvhuff                 pcm_f64le               vp9_vaapi
fits                    pcm_mulaw               wavpack
flac                    pcm_s16be               wbmp
flashsv                 pcm_s16be_planar        webvtt
flashsv2                pcm_s16le               wmav1
flv                     pcm_s16le_planar        wmav2
g723_1                  pcm_s24be               wmv1
gif                     pcm_s24daud             wmv2
h261                    pcm_s24le               wrapped_avframe
h263                    pcm_s24le_planar        xbm
h263p                   pcm_s32be               xface
h264_amf                pcm_s32le               xsub
h264_mf                 pcm_s32le_planar        xwd
h264_nvenc              pcm_s64be               y41p
h264_qsv                pcm_s64le               yuv4
h264_vaapi              pcm_s8                  zlib
hdr                     pcm_s8_planar           zmbv
hevc_amf                pcm_u16be

Enabled hwaccels:
av1_d3d11va             hevc_nvdec              vc1_nvdec
av1_d3d11va2            hevc_vaapi              vc1_vaapi
av1_d3d12va             mjpeg_nvdec             vp8_nvdec
av1_dxva2               mjpeg_vaapi             vp8_vaapi
av1_nvdec               mpeg1_nvdec             vp9_d3d11va
av1_vaapi               mpeg2_d3d11va           vp9_d3d11va2
h263_vaapi              mpeg2_d3d11va2          vp9_d3d12va
h264_d3d11va            mpeg2_d3d12va           vp9_dxva2
h264_d3d11va2           mpeg2_dxva2             vp9_nvdec
h264_d3d12va            mpeg2_nvdec             vp9_vaapi
h264_dxva2              mpeg2_vaapi             vvc_vaapi
h264_nvdec              mpeg4_nvdec             wmv3_d3d11va
h264_vaapi              mpeg4_vaapi             wmv3_d3d11va2
hevc_d3d11va            vc1_d3d11va             wmv3_d3d12va
hevc_d3d11va2           vc1_d3d11va2            wmv3_dxva2
hevc_d3d12va            vc1_d3d12va             wmv3_nvdec
hevc_dxva2              vc1_dxva2               wmv3_vaapi

Enabled parsers:
aac                     dvd_nav                 mpeg4video
aac_latm                dvdsub                  mpegaudio
ac3                     evc                     mpegvideo
adx                     ffv1                    opus
amr                     flac                    png
apv                     ftr                     pnm
av1                     g723_1                  qoi
avs2                    g729                    rv34
avs3                    gif                     sbc
bmp                     gsm                     sipr
cavsvideo               h261                    tak
cook                    h263                    vc1
cri                     h264                    vorbis
dca                     hdr                     vp3
dirac                   hevc                    vp8
dnxhd                   ipu                     vp9
dnxuc                   jpeg2000                vvc
dolby_e                 jpegxl                  webp
dpx                     misc4                   xbm
dvaudio                 mjpeg                   xma
dvbsub                  mlp                     xwd

Enabled demuxers:
aa                      idcin                   pcm_f64le
aac                     idf                     pcm_mulaw
aax                     iff                     pcm_s16be
ac3                     ifv                     pcm_s16le
ac4                     ilbc                    pcm_s24be
ace                     image2                  pcm_s24le
acm                     image2_alias_pix        pcm_s32be
act                     image2_brender_pix      pcm_s32le
adf                     image2pipe              pcm_s8
adp                     image_bmp_pipe          pcm_u16be
ads                     image_cri_pipe          pcm_u16le
adx                     image_dds_pipe          pcm_u24be
aea                     image_dpx_pipe          pcm_u24le
afc                     image_exr_pipe          pcm_u32be
aiff                    image_gem_pipe          pcm_u32le
aix                     image_gif_pipe          pcm_u8
alp                     image_hdr_pipe          pcm_vidc
amr                     image_j2k_pipe          pdv
amrnb                   image_jpeg_pipe         pjs
amrwb                   image_jpegls_pipe       pmp
anm                     image_jpegxl_pipe       pp_bnk
apac                    image_pam_pipe          pva
apc                     image_pbm_pipe          pvf
ape                     image_pcx_pipe          qcp
apm                     image_pfm_pipe          qoa
apng                    image_pgm_pipe          r3d
aptx                    image_pgmyuv_pipe       rawvideo
aptx_hd                 image_pgx_pipe          rcwt
apv                     image_phm_pipe          realtext
aqtitle                 image_photocd_pipe      redspark
argo_asf                image_pictor_pipe       rka
argo_brp                image_png_pipe          rl2
argo_cvg                image_ppm_pipe          rm
asf                     image_psd_pipe          roq
asf_o                   image_qdraw_pipe        rpl
ass                     image_qoi_pipe          rsd
ast                     image_sgi_pipe          rso
au                      image_sunrast_pipe      rtp
av1                     image_svg_pipe          rtsp
avi                     image_tiff_pipe         s337m
avisynth                image_vbn_pipe          sami
avr                     image_webp_pipe         sap
avs                     image_xbm_pipe          sbc
avs2                    image_xpm_pipe          sbg
avs3                    image_xwd_pipe          scc
bethsoftvid             imf                     scd
bfi                     ingenient               sdns
bfstm                   ipmovie                 sdp
bink                    ipu                     sdr2
binka                   ircam                   sds
bintext                 iss                     sdx
bit                     iv8                     segafilm
bitpacked               ivf                     ser
bmv                     ivr                     sga
boa                     jacosub                 shorten
bonk                    jpegxl_anim             siff
brstm                   jv                      simbiosis_imx
c93                     kux                     sln
caf                     kvag                    smacker
cavsvideo               laf                     smjpeg
cdg                     lc3                     smush
cdxl                    libgme                  sol
cine                    libopenmpt              sox
codec2                  live_flv                spdif
codec2raw               lmlm4                   srt
concat                  loas                    stl
dash                    lrc                     str
data                    luodat                  subviewer
daud                    lvf                     subviewer1
dcstr                   lxf                     sup
derf                    m4v                     svag
dfa                     matroska                svs
dfpwm                   mca                     swf
dhav                    mcc                     tak
dirac                   mgsts                   tedcaptions
dnxhd                   microdvd                thp
dsf                     mjpeg                   threedostr
dsicin                  mjpeg_2000              tiertexseq
dss                     mlp                     tmv
dts                     mlv                     truehd
dtshd                   mm                      tta
dv                      mmf                     tty
dvbsub                  mods                    txd
dvbtxt                  moflex                  ty
dxa                     mov                     usm
ea                      mp3                     v210
ea_cdata                mpc                     v210x
eac3                    mpc8                    vag
epaf                    mpegps                  vc1
evc                     mpegts                  vc1t
ffmetadata              mpegtsraw               vividas
filmstrip               mpegvideo               vivo
fits                    mpjpeg                  vmd
flac                    mpl2                    vobsub
flic                    mpsub                   voc
flv                     msf                     vpk
fourxm                  msnwc_tcp               vplayer
frm                     msp                     vqf
fsb                     mtaf                    vvc
fwse                    mtv                     w64
g722                    musx                    wady
g723_1                  mv                      wav
g726                    mvi                     wavarc
g726le                  mxf                     wc3
g729                    mxg                     webm_dash_manifest
gdv                     nc                      webvtt
genh                    nistsphere              wsaud
gif                     nsp                     wsd
gsm                     nsv                     wsvqa
gxf                     nut                     wtv
h261                    nuv                     wv
h263                    obu                     wve
h264                    ogg                     xa
hca                     oma                     xbin
hcom                    osq                     xmd
hevc                    paf                     xmv
hls                     pcm_alaw                xvag
hnm                     pcm_f32be               xwma
iamf                    pcm_f32le               yop
ico                     pcm_f64be               yuv4mpegpipe

Enabled muxers:
a64                     h263                    pcm_s24be
ac3                     h264                    pcm_s24le
ac4                     hash                    pcm_s32be
adts                    hds                     pcm_s32le
adx                     hevc                    pcm_s8
aea                     hls                     pcm_u16be
aiff                    iamf                    pcm_u16le
alp                     ico                     pcm_u24be
amr                     ilbc                    pcm_u24le
amv                     image2                  pcm_u32be
apm                     image2pipe              pcm_u32le
apng                    ipod                    pcm_u8
aptx                    ircam                   pcm_vidc
aptx_hd                 ismv                    psp
apv                     ivf                     rawvideo
argo_asf                jacosub                 rcwt
argo_cvg                kvag                    rm
asf                     latm                    roq
asf_stream              lc3                     rso
ass                     lrc                     rtp
ast                     m4v                     rtp_mpegts
au                      matroska                rtsp
avi                     matroska_audio          sap
avif                    md5                     sbc
avm2                    microdvd                scc
avs2                    mjpeg                   segafilm
avs3                    mkvtimestamp_v2         segment
bit                     mlp                     smjpeg
caf                     mmf                     smoothstreaming
cavsvideo               mov                     sox
codec2                  mp2                     spdif
codec2raw               mp3                     spx
crc                     mp4                     srt
dash                    mpeg1system             stream_segment
data                    mpeg1vcd                streamhash
daud                    mpeg1video              sup
dfpwm                   mpeg2dvd                swf
dirac                   mpeg2svcd               tee
dnxhd                   mpeg2video              tg2
dts                     mpeg2vob                tgp
dv                      mpegts                  truehd
eac3                    mpjpeg                  tta
evc                     mxf                     ttml
f4v                     mxf_d10                 uncodedframecrc
ffmetadata              mxf_opatom              vc1
fifo                    null                    vc1t
filmstrip               nut                     voc
fits                    obu                     vvc
flac                    oga                     w64
flv                     ogg                     wav
framecrc                ogv                     webm
framehash               oma                     webm_chunk
framemd5                opus                    webm_dash_manifest
g722                    pcm_alaw                webp
g723_1                  pcm_f32be               webvtt
g726                    pcm_f32le               wsaud
g726le                  pcm_f64be               wtv
gif                     pcm_f64le               wv
gsm                     pcm_mulaw               yuv4mpegpipe
gxf                     pcm_s16be
h261                    pcm_s16le

Enabled protocols:
async                   http                    rtmp
cache                   httpproxy               rtmpe
concat                  https                   rtmps
concatf                 icecast                 rtmpt
crypto                  ipfs_gateway            rtmpte
data                    ipns_gateway            rtmpts
fd                      libsrt                  rtp
ffrtmpcrypt             libssh                  srtp
ffrtmphttp              libzmq                  subfile
file                    md5                     tcp
ftp                     mmsh                    tee
gopher                  mmst                    tls
gophers                 pipe                    udp
hls                     prompeg                 udplite

Enabled filters:
a3dscope                datascope               pan
aap                     dblur                   perlin
abench                  dcshift                 perms
abitscope               dctdnoiz                perspective
acompressor             ddagrab                 phase
acontrast               deband                  photosensitivity
acopy                   deblock                 pixdesctest
acrossfade              decimate                pixelize
acrossover              deconvolve              pixscope
acrusher                dedot                   pp7
acue                    deesser                 premultiply
addroi                  deflate                 prewitt
adeclick                deflicker               procamp_vaapi
adeclip                 deinterlace_qsv         pseudocolor
adecorrelate            deinterlace_vaapi       psnr
adelay                  dejudder                pullup
adenorm                 delogo                  qp
aderivative             denoise_vaapi           random
adrawgraph              deshake                 readeia608
adrc                    despill                 readvitc
adynamicequalizer       detelecine              realtime
adynamicsmooth          dialoguenhance          remap
aecho                   dilation                removegrain
aemphasis               displace                removelogo
aeval                   doubleweave             repeatfields
aevalsrc                drawbox                 replaygain
aexciter                drawbox_vaapi           reverse
afade                   drawgraph               rgbashift
afdelaysrc              drawgrid                rgbtestsrc
afftdn                  drawtext                roberts
afftfilt                drmeter                 rotate
afir                    dynaudnorm              rubberband
afireqsrc               earwax                  sab
afirsrc                 ebur128                 scale
aformat                 edgedetect              scale2ref
afreqshift              elbg                    scale_cuda
afwtdn                  entropy                 scale_qsv
agate                   epx                     scale_vaapi
agraphmonitor           eq                      scdet
ahistogram              equalizer               scharr
aiir                    erosion                 scroll
aintegral               estdif                  segment
ainterleave             exposure                select
alatency                extractplanes           selectivecolor
alimiter                extrastereo             sendcmd
allpass                 fade                    separatefields
allrgb                  feedback                setdar
allyuv                  fftdnoiz                setfield
aloop                   fftfilt                 setparams
alphaextract            field                   setpts
alphamerge              fieldhint               setrange
amerge                  fieldmatch              setsar
ametadata               fieldorder              settb
amix                    fillborders             sharpness_vaapi
amovie                  find_rect               shear
amplify                 firequalizer            showcqt
amultiply               flanger                 showcwt
anequalizer             floodfill               showfreqs
anlmdn                  format                  showinfo
anlmf                   fps                     showpalette
anlms                   framepack               showspatial
anoisesrc               framerate               showspectrum
anull                   framestep               showspectrumpic
anullsink               freezedetect            showvolume
anullsrc                freezeframes            showwaves
apad                    fspp                    showwavespic
aperms                  fsync                   shuffleframes
aphasemeter             gblur                   shufflepixels
aphaser                 geq                     shuffleplanes
aphaseshift             gradfun                 sidechaincompress
apsnr                   gradients               sidechaingate
apsyclip                graphmonitor            sidedata
apulsator               grayworld               sierpinski
arealtime               greyedge                signalstats
aresample               guided                  signature
areverse                haas                    silencedetect
arls                    haldclut                silenceremove
arnndn                  haldclutsrc             sinc
asdr                    hdcd                    sine
asegment                headphone               siti
aselect                 hflip                   smartblur
asendcmd                highpass                smptebars
asetnsamples            highshelf               smptehdbars
asetpts                 hilbert                 sobel
asetrate                histeq                  spectrumsynth
asettb                  histogram               speechnorm
ashowinfo               hqdn3d                  split
asidedata               hqx                     spp
asisdr                  hstack                  sr_amf
asoftclip               hstack_qsv              ssim
aspectralstats          hstack_vaapi            ssim360
asplit                  hsvhold                 stereo3d
ass                     hsvkey                  stereotools
astats                  hue                     stereowiden
astreamselect           huesaturation           streamselect
asubboost               hwdownload              subtitles
asubcut                 hwmap                   super2xsai
asupercut               hwupload                superequalizer
asuperpass              hwupload_cuda           surround
asuperstop              hysteresis              swaprect
atadenoise              identity                swapuv
atempo                  idet                    tblend
atilt                   il                      telecine
atrim                   inflate                 testsrc
avectorscope            interlace               testsrc2
avgblur                 interleave              thistogram
avsynctest              join                    threshold
axcorrelate             kerndeint               thumbnail
azmq                    kirsch                  thumbnail_cuda
backgroundkey           lagfun                  tile
bandpass                latency                 tiltandshift
bandreject              lenscorrection          tiltshelf
bass                    libvmaf                 tinterlace
bbox                    life                    tlut2
bench                   limitdiff               tmedian
bilateral               limiter                 tmidequalizer
bilateral_cuda          loop                    tmix
biquad                  loudnorm                tonemap
bitplanenoise           lowpass                 tonemap_vaapi
blackdetect             lowshelf                tpad
blackframe              lumakey                 transpose
blend                   lut                     transpose_vaapi
blockdetect             lut1d                   treble
blurdetect              lut2                    tremolo
bm3d                    lut3d                   trim
boxblur                 lutrgb                  unpremultiply
bwdif                   lutyuv                  unsharp
bwdif_cuda              mandelbrot              untile
cas                     maskedclamp             uspp
ccrepack                maskedmax               v360
cellauto                maskedmerge             vaguedenoiser
channelmap              maskedmin               varblur
channelsplit            maskedthreshold         vectorscope
chorus                  maskfun                 vflip
chromahold              mcdeint                 vfrdet
chromakey               mcompand                vibrance
chromakey_cuda          median                  vibrato
chromanr                mergeplanes             vidstabdetect
chromashift             mestimate               vidstabtransform
ciescope                metadata                vif
codecview               midequalizer            vignette
color                   minterpolate            virtualbass
colorbalance            mix                     vmafmotion
colorchannelmixer       monochrome              volume
colorchart              morpho                  volumedetect
colorcontrast           movie                   vpp_amf
colorcorrect            mpdecimate              vpp_qsv
colorhold               mptestsrc               vstack
colorize                msad                    vstack_qsv
colorkey                multiply                vstack_vaapi
colorlevels             negate                  w3fdif
colormap                nlmeans                 waveform
colormatrix             nnedi                   weave
colorspace              noformat                xbr
colorspace_cuda         noise                   xcorrelate
colorspectrum           normalize               xfade
colortemperature        null                    xmedian
compand                 nullsink                xpsnr
compensationdelay       nullsrc                 xstack
concat                  oscilloscope            xstack_qsv
convolution             overlay                 xstack_vaapi
convolve                overlay_cuda            yadif
copy                    overlay_qsv             yadif_cuda
corr                    overlay_vaapi           yaepblur
cover_rect              owdenoise               yuvtestsrc
crop                    pad                     zmq
cropdetect              pad_vaapi               zoneplate
crossfeed               pal100bars              zoompan
crystalizer             pal75bars               zscale
cue                     palettegen
curves                  paletteuse

Enabled bsfs:
aac_adtstoasc           h264_mp4toannexb        pgs_frame_merge
apv_metadata            h264_redundant_pps      prores_metadata
av1_frame_merge         hapqa_extract           remove_extradata
av1_frame_split         hevc_metadata           setts
av1_metadata            hevc_mp4toannexb        showinfo
chomp                   imx_dump_header         text2movsub
dca_core                media100_to_mjpegb      trace_headers
dovi_rpu                mjpeg2jpeg              truehd_core
dts2pts                 mjpega_dump_header      vp9_metadata
dump_extradata          mov2textsub             vp9_raw_reorder
dv_error_marker         mpeg2_metadata          vp9_superframe
eac3_core               mpeg4_unpack_bframes    vp9_superframe_split
evc_frame_merge         noise                   vvc_metadata
extract_extradata       null                    vvc_mp4toannexb
filter_units            opus_metadata
h264_metadata           pcm_rechunk

Enabled indevs:
dshow                   lavfi
gdigrab                 vfwcap

Enabled outdevs:

git-essentials external libraries' versions: 

AMF v1.4.36-2-gd7311e3
aom v3.12.1-135-gb9f374fae1
AviSynthPlus v3.7.5-14-g7bbd0a63
ffnvcodec n13.0.19.0-1-gf2fb9b3
freetype VER-2-13-3
fribidi v1.0.16-2-gb28f43b
gsm 1.0.22
harfbuzz 11.2.0-66-gadf11168
lame 3.100
libass 0.17.3-81-g6955093
libgme 0.6.3
libopencore-amrnb 0.1.6
libopencore-amrwb 0.1.6
libssh 0.11.1
libtheora 1.2.0
libwebp v1.5.0-42-geb3ff781
openmpt libopenmpt-0.6.22-24-g821723f93
opus v1.5.2-106-g08bcc6e4
rubberband v1.8.1
SDL release-2.32.0-47-g2163887f2
speex Speex-1.2.1-47-ga145463
srt v1.5.4-31-g952f949
VAAPI 2.23.0.
vidstab v1.1.1-14-gd2d55a8
vmaf v3.0.0-112-gb9ac69e6
vo-amrwbenc 0.1.3
vorbis v1.3.7-10-g84c02369
VPL 2.15
vpx v1.15.1-85-g37c2802fb
x264 v0.165.3215
x265 4.1-158-g78e5ac35c
xvid v1.3.7
zeromq 4.3.5
zimg release-3.0.5-204-g2a1c3e2

