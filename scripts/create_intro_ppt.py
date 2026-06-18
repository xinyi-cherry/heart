import html
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "心率助手功能介绍.pptx"
HERO = ROOT / "site" / "assets" / "hero-heart-assistant.png"

SLIDE_W = 12192000
SLIDE_H = 6858000


def emu(inches: float) -> int:
    return int(inches * 914400)


def esc(text: str) -> str:
    return html.escape(text, quote=True)


class Deck:
    def __init__(self):
        self.files: dict[str, bytes | str] = {}
        self.slide_count = 0

    def add(self, name: str, content: bytes | str) -> None:
        self.files[name] = content

    def write(self) -> None:
        if OUT.exists():
            OUT.unlink()
        with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in self.files.items():
                archive.writestr(name, content)


def color(hex_color: str) -> str:
    return hex_color.strip("#").upper()


def solid_fill(hex_color: str) -> str:
    return f'<a:solidFill><a:srgbClr val="{color(hex_color)}"/></a:solidFill>'


def shape(
    shape_id: int,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str = "FFFFFF",
    radius: str = "roundRect",
    line: str | None = None,
    alpha: int | None = None,
) -> str:
    fill_xml = solid_fill(fill)
    if alpha is not None:
        fill_xml = (
            f'<a:solidFill><a:srgbClr val="{color(fill)}">'
            f'<a:alpha val="{alpha}"/></a:srgbClr></a:solidFill>'
        )
    line_xml = '<a:ln><a:noFill/></a:ln>' if line is None else f'<a:ln w="12700">{solid_fill(line)}</a:ln>'
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{shape_id}" name="Shape {shape_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
        <a:prstGeom prst="{radius}"><a:avLst/></a:prstGeom>
        {fill_xml}
        {line_xml}
      </p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
    </p:sp>
    """


def text_box(
    shape_id: int,
    x: float,
    y: float,
    w: float,
    h: float,
    lines: list[str],
    size: int = 24,
    fill: str = "102033",
    bold: bool = False,
    align: str = "l",
    spacing: int = 90,
) -> str:
    paras = []
    for line in lines:
        if not line:
            paras.append("<a:p/>")
            continue
        paras.append(
            f"""
            <a:p>
              <a:pPr algn="{align}"/>
              <a:r>
                <a:rPr lang="zh-CN" sz="{size * 100}" b="{1 if bold else 0}" dirty="0">
                  {solid_fill(fill)}
                  <a:latin typeface="Microsoft YaHei"/>
                  <a:ea typeface="Microsoft YaHei"/>
                </a:rPr>
                <a:t>{esc(line)}</a:t>
              </a:r>
              <a:endParaRPr lang="zh-CN" sz="{size * 100}" dirty="0"/>
            </a:p>
            """
        )
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{shape_id}" name="Text {shape_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        <a:noFill/><a:ln><a:noFill/></a:ln>
      </p:spPr>
      <p:txBody>
        <a:bodyPr wrap="square" lIns="{spacing}" tIns="{spacing}" rIns="{spacing}" bIns="{spacing}"/>
        <a:lstStyle/>
        {''.join(paras)}
      </p:txBody>
    </p:sp>
    """


def bullet_list(shape_id: int, x: float, y: float, w: float, h: float, items: list[str]) -> str:
    paras = []
    for item in items:
        paras.append(
            f"""
            <a:p>
              <a:pPr marL="285750" indent="-171450"/>
              <a:r>
                <a:rPr lang="zh-CN" sz="2100" dirty="0">
                  {solid_fill("16A34A")}
                  <a:latin typeface="Microsoft YaHei"/>
                  <a:ea typeface="Microsoft YaHei"/>
                </a:rPr>
                <a:t>●</a:t>
              </a:r>
              <a:r>
                <a:rPr lang="zh-CN" sz="2100" dirty="0">
                  {solid_fill("334155")}
                  <a:latin typeface="Microsoft YaHei"/>
                  <a:ea typeface="Microsoft YaHei"/>
                </a:rPr>
                <a:t>  {esc(item)}</a:t>
              </a:r>
            </a:p>
            """
        )
    return text_container(shape_id, x, y, w, h, "".join(paras))


def text_container(shape_id: int, x: float, y: float, w: float, h: float, paras: str) -> str:
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{shape_id}" name="Bullets {shape_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        <a:noFill/><a:ln><a:noFill/></a:ln>
      </p:spPr>
      <p:txBody>
        <a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0"/>
        <a:lstStyle/>
        {paras}
      </p:txBody>
    </p:sp>
    """


def picture(shape_id: int, rel_id: str, x: float, y: float, w: float, h: float) -> str:
    return f"""
    <p:pic>
      <p:nvPicPr><p:cNvPr id="{shape_id}" name="Hero image"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
      <p:blipFill>
        <a:blip r:embed="{rel_id}"/>
        <a:stretch><a:fillRect/></a:stretch>
      </p:blipFill>
      <p:spPr>
        <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
        <a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>
      </p:spPr>
    </p:pic>
    """


def base_slide(shapes: list[str], bg: str = "F6F8FC") -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr>{solid_fill(bg)}<a:effectLst/></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {''.join(shapes)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def add_title(slide: list[str], title: str, subtitle: str | None = None) -> None:
    slide.append(text_box(10, 0.65, 0.45, 7.4, 0.55, ["心率助手"], 16, "16A34A", True))
    slide.append(text_box(11, 0.65, 0.92, 8.6, 0.8, [title], 34, "102033", True))
    if subtitle:
        slide.append(text_box(12, 0.68, 1.72, 9.2, 0.48, [subtitle], 17, "64748B"))


def add_step_card(slide: list[str], sid: int, x: float, y: float, w: float, num: str, title: str, body: str) -> None:
    slide.append(shape(sid, x, y, w, 1.08, "FFFFFF", line="DDE7F2"))
    slide.append(shape(sid + 1, x + 0.18, y + 0.21, 0.5, 0.5, "DCFCE7", "roundRect", None))
    slide.append(text_box(sid + 2, x + 0.18, y + 0.24, 0.5, 0.3, [num], 15, "15803D", True, "ctr"))
    slide.append(text_box(sid + 3, x + 0.82, y + 0.16, w - 1.0, 0.32, [title], 16, "102033", True))
    slide.append(text_box(sid + 4, x + 0.82, y + 0.53, w - 1.0, 0.38, [body], 12, "64748B"))


def add_slides(deck: Deck) -> None:
    slides: list[tuple[str, str]] = []

    s = [
        shape(20, 0, 0, 13.333, 7.5, "0F172A", "rect"),
        picture(21, "rIdImg1", 6.72, 0.52, 5.95, 4.98),
        shape(22, 0.55, 0.62, 5.75, 5.35, "0B1220", "roundRect", None, 82000),
        text_box(23, 0.82, 0.96, 4.8, 0.4, ["智能手环心率输出工具"], 18, "86EFAC", True),
        text_box(24, 0.78, 1.48, 5.25, 1.02, ["心率助手"], 44, "FFFFFF", True),
        text_box(25, 0.82, 2.62, 5.2, 1.1, ["从手环读取实时心率，并写入直播或自动化工具可读取的输出文件。"], 21, "D8E5F4"),
        shape(26, 0.88, 4.08, 1.3, 0.42, "16A34A"),
        text_box(27, 0.97, 4.14, 1.1, 0.22, ["BLE"], 13, "FFFFFF", True, "ctr"),
        shape(28, 2.33, 4.08, 1.75, 0.42, "1D4ED8"),
        text_box(29, 2.42, 4.14, 1.55, 0.22, ["三平台"], 13, "FFFFFF", True, "ctr"),
        shape(30, 4.23, 4.08, 1.7, 0.42, "EF6F5E"),
        text_box(31, 4.32, 4.14, 1.5, 0.22, ["直播可用"], 13, "FFFFFF", True, "ctr"),
    ]
    slides.append((base_slide(s, "0F172A"), slide_rels("rIdImg1")))

    s = []
    add_title(s, "整体流程", "准备好手环、软件和直播工具后，按顺序完成连接与文本读取。")
    steps = [
        ("01", "工具准备", "下载心率助手，准备支持心率广播的手环或手表。"),
        ("02", "开启广播", "在官方 App 或设备设置中打开心率广播功能。"),
        ("03", "连接设备", "打开软件，选择推荐度高的设备并开始记录。"),
        ("04", "接入直播", "在直播姬或 OBS 中读取输出文件并显示心率。"),
    ]
    for i, item in enumerate(steps):
        add_step_card(s, 40 + i * 10, 0.9, 2.28 + i * 1.05, 11.2, *item)
    slides.append((base_slide(s), empty_rels()))

    s = []
    add_title(s, "工具准备", "提前确认设备、权限和输出路径，后续连接会顺很多。")
    s.append(shape(90, 0.75, 2.05, 3.8, 3.45, "FFFFFF", line="DDE7F2"))
    s.append(shape(91, 4.78, 2.05, 3.8, 3.45, "FFFFFF", line="DDE7F2"))
    s.append(shape(92, 8.8, 2.05, 3.8, 3.45, "FFFFFF", line="DDE7F2"))
    s.append(text_box(93, 1.05, 2.35, 3.2, 0.38, ["心率助手"], 22, "102033", True, "ctr"))
    s.append(text_box(94, 5.08, 2.35, 3.2, 0.38, ["手环 / 手表"], 22, "102033", True, "ctr"))
    s.append(text_box(95, 9.1, 2.35, 3.2, 0.38, ["直播软件"], 22, "102033", True, "ctr"))
    s.append(bullet_list(96, 1.05, 3.05, 3.2, 1.6, ["下载对应系统版本", "确认电脑蓝牙可用", "准备输出文件位置"]))
    s.append(bullet_list(97, 5.08, 3.05, 3.2, 1.6, ["电量充足", "佩戴并开始测量", "支持标准心率广播更佳"]))
    s.append(bullet_list(98, 9.1, 3.05, 3.2, 1.6, ["直播姬或 OBS", "添加文本来源", "设置字体和位置"]))
    slides.append((base_slide(s), empty_rels()))

    s = []
    add_title(s, "打开心率广播", "很多手环默认不会持续广播心率，需要手动开启第三方设备连接。")
    s.append(shape(120, 0.9, 2.02, 5.35, 3.75, "FFFFFF", line="DDE7F2"))
    s.append(text_box(121, 1.22, 2.34, 4.75, 0.4, ["常见入口名称"], 24, "102033", True))
    s.append(bullet_list(122, 1.25, 3.05, 4.45, 1.7, ["心率广播", "蓝牙心率广播", "第三方设备连接", "运动设备 / 外部设备连接"]))
    s.append(shape(123, 6.72, 2.02, 5.45, 3.75, "ECFDF5", line="BBF7D0"))
    s.append(text_box(124, 7.1, 2.42, 4.6, 0.52, ["关键提示"], 25, "15803D", True))
    s.append(text_box(125, 7.1, 3.18, 4.75, 1.35, ["开启后保持手环贴合手腕。若列表中看不到设备，可以先在手环上开始一次运动或心率测量。"], 20, "166534"))
    slides.append((base_slide(s), empty_rels()))

    s = []
    add_title(s, "打开软件连接手环", "软件会自动刷新附近设备，优先展示更可能是心率设备的项目。")
    add_step_card(s, 150, 0.9, 2.25, 5.45, "1", "等待自动刷新", "列表每 5 秒刷新一次，也可以点击“立即扫描”。")
    add_step_card(s, 160, 6.75, 2.25, 5.45, "2", "选择推荐设备", "优先选择推荐度高、名称接近手环型号的设备。")
    add_step_card(s, 170, 0.9, 3.75, 5.45, "3", "连接并记录", "点击“连接并记录”，状态变为记录中后开始接收心率。")
    add_step_card(s, 180, 6.75, 3.75, 5.45, "4", "观察日志", "如果报错，回到手环设置确认广播功能已开启。")
    slides.append((base_slide(s), empty_rels()))

    s = []
    add_title(s, "设置输出文件位置和格式", "直播工具读取的是这个输出文件，因此文件路径和格式要提前确定。")
    s.append(shape(210, 0.95, 2.1, 5.15, 3.65, "FFFFFF", line="DDE7F2"))
    s.append(text_box(211, 1.27, 2.42, 4.5, 0.4, ["输出设置"], 24, "102033", True))
    s.append(bullet_list(212, 1.25, 3.12, 4.45, 1.4, ["选择一个固定位置的输出文件", "按需要填写前缀和后缀", "输出预览会显示最终文本格式"]))
    s.append(shape(213, 6.72, 2.1, 5.55, 3.65, "0F172A", line=None))
    s.append(text_box(214, 7.1, 2.5, 4.75, 0.38, ["输出示例"], 22, "86EFAC", True))
    s.append(text_box(215, 7.1, 3.15, 4.75, 0.78, ["72"], 44, "FFFFFF", True, "ctr"))
    s.append(text_box(216, 7.1, 4.15, 4.75, 0.4, ["或 HR=72 bpm"], 24, "D8E5F4", True, "ctr"))
    s.append(text_box(217, 7.1, 4.9, 4.75, 0.36, ["每次收到新心率都会覆盖写入最新值"], 15, "CBD5E1", False, "ctr"))
    slides.append((base_slide(s), empty_rels()))

    s = []
    add_title(s, "在直播姬中添加心率", "将输出文件作为文本来源读取，再把它放到直播画面合适的位置。")
    add_step_card(s, 240, 0.9, 2.0, 11.2, "1", "添加文本来源", "在场景中新增文本或本地文本来源。")
    add_step_card(s, 250, 0.9, 3.05, 11.2, "2", "选择心率助手输出文件", "文件路径选择软件中设置的同一个输出文件。")
    add_step_card(s, 260, 0.9, 4.1, 11.2, "3", "调整样式", "设置字体、颜色、字号和位置，例如放在角色旁或信息栏中。")
    s.append(shape(270, 0.9, 5.5, 11.2, 0.55, "FFF7ED", line="FED7AA"))
    s.append(text_box(271, 1.1, 5.61, 10.8, 0.22, ["如果直播姬没有实时更新，检查文本来源是否开启了文件内容刷新。"], 14, "9A3412"))
    slides.append((base_slide(s), empty_rels()))

    s = []
    add_title(s, "在 OBS 中添加心率", "OBS 推荐使用文本来源读取文件，心率助手负责持续更新文件内容。")
    s.append(shape(300, 0.95, 2.05, 5.45, 3.7, "FFFFFF", line="DDE7F2"))
    s.append(text_box(301, 1.28, 2.38, 4.8, 0.38, ["OBS 操作"], 24, "102033", True))
    s.append(bullet_list(302, 1.28, 3.1, 4.7, 1.6, ["来源 → 文本", "勾选“从文件读取”", "选择输出文件", "设置字体、颜色和描边"]))
    s.append(shape(303, 6.9, 2.05, 5.1, 3.7, "F0FDF4", line="BBF7D0"))
    s.append(text_box(304, 7.24, 2.38, 4.45, 0.38, ["推荐展示格式"], 24, "15803D", True))
    s.append(text_box(305, 7.24, 3.18, 4.45, 0.62, ["心率 72 bpm"], 34, "166534", True, "ctr"))
    s.append(text_box(306, 7.24, 4.16, 4.45, 0.62, ["可以配合前缀/后缀在心率助手里直接生成完整文本。"], 18, "166534", False, "ctr"))
    slides.append((base_slide(s), empty_rels()))

    for i, (slide_xml, rels_xml) in enumerate(slides, start=1):
        deck.add(f"ppt/slides/slide{i}.xml", slide_xml)
        deck.add(f"ppt/slides/_rels/slide{i}.xml.rels", rels_xml)


def empty_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>"""


def slide_rels(image_rel_id: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="{image_rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/hero-heart-assistant.png"/>
</Relationships>"""


def content_types(slide_count: int) -> str:
    slides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  {slides}
</Types>"""


def presentation(slide_count: int) -> str:
    ids = "\n".join(
        f'<p:sldId id="{255 + i}" r:id="rId{i}"/>' for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rIdMaster"/></p:sldMasterIdLst>
  <p:sldIdLst>{ids}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle/>
</p:presentation>"""


def presentation_rels(slide_count: int) -> str:
    slide_rels_xml = "\n".join(
        f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {slide_rels_xml}
  <Relationship Id="rIdMaster" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
  <Relationship Id="rIdTheme" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
</Relationships>"""


def package_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""


def slide_master() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
  </p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""


def slide_master_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""


def slide_layout() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""


def slide_layout_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""


def theme() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Heart Assistant">
  <a:themeElements>
    <a:clrScheme name="Heart Assistant">
      <a:dk1><a:srgbClr val="102033"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="334155"/></a:dk2><a:lt2><a:srgbClr val="F6F8FC"/></a:lt2>
      <a:accent1><a:srgbClr val="16A34A"/></a:accent1><a:accent2><a:srgbClr val="165DFF"/></a:accent2>
      <a:accent3><a:srgbClr val="EF6F5E"/></a:accent3><a:accent4><a:srgbClr val="B7791F"/></a:accent4>
      <a:accent5><a:srgbClr val="64748B"/></a:accent5><a:accent6><a:srgbClr val="DDE7F2"/></a:accent6>
      <a:hlink><a:srgbClr val="165DFF"/></a:hlink><a:folHlink><a:srgbClr val="64748B"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Heart Assistant"><a:majorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:majorFont><a:minorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Heart Assistant"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
</a:theme>"""


def main() -> int:
    if not HERO.exists():
        raise FileNotFoundError(f"Missing hero image: {HERO}")

    deck = Deck()
    add_slides(deck)
    slide_count = 8
    deck.add("[Content_Types].xml", content_types(slide_count))
    deck.add("_rels/.rels", package_rels())
    deck.add("ppt/presentation.xml", presentation(slide_count))
    deck.add("ppt/_rels/presentation.xml.rels", presentation_rels(slide_count))
    deck.add("ppt/slideMasters/slideMaster1.xml", slide_master())
    deck.add("ppt/slideMasters/_rels/slideMaster1.xml.rels", slide_master_rels())
    deck.add("ppt/slideLayouts/slideLayout1.xml", slide_layout())
    deck.add("ppt/slideLayouts/_rels/slideLayout1.xml.rels", slide_layout_rels())
    deck.add("ppt/theme/theme1.xml", theme())
    deck.add("ppt/media/hero-heart-assistant.png", HERO.read_bytes())
    deck.write()
    print(f"Created: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
