import io
import networkx as nx
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from pathlib import Path

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="복도 최단 경로 시뮬레이터", layout="wide")



# ===== Streamlit 고정 배지/브랜딩 요소 전부 숨기기 =====
HIDE_BRANDING = """
<style>
/* 기본 메뉴, 헤더, 푸터 제거 */
#MainMenu {display: none !important;}
header {display: none !important;}
footer {display: none !important;}

/* Streamlit 배지/브랜딩 요소 제거 */
div[data-testid*="stDecoration"] {display: none !important;}
div[class*="viewerBadge"] {display: none !important;}
div[data-testid="stStatusWidget"] {display: none !important;}

/* a태그 중 Streamlit 관련 링크 제거 */
a[href*="streamlit.io"] {display: none !important;}
a[href*="streamlit.app"] {display: none !important;}

/* iframe에 포함된 경우도 숨기기 */
iframe[src*="streamlit.io"] {display: none !important;}
iframe[src*="streamlit.app"] {display: none !important;}

/* 버튼/아이콘(왕관, 프로필 등) 제거 */
button[title*="Streamlit"] {display: none !important;}
button[title*="Manage"] {display: none !important;}
svg[data-testid="iconCrownsFilled"] {display: none !important;}
svg[data-testid="iconProfileCircle"] {display: none !important;}
</style>
"""
st.markdown(HIDE_BRANDING, unsafe_allow_html=True)

# 좌표가 설계된 원본 지도 기준 크기 (고정)
BASE_W, BASE_H = 800, 600

# =========================
# 한글 폰트 로더 (단일)
# =========================
@st.cache_resource
def _load_korean_font(size=20):
    font_path = Path(__file__).parent / "NotoSansKR-Regular.ttf"  # 같은 폴더에 있을 경우
    try:
        return ImageFont.truetype(str(font_path), size=size)
    except Exception as e:
        st.error(f"폰트 로드 실패: {e}")
        return ImageFont.load_default()


# =========================
# 데이터 정의 (원본 유지)
# =========================
classroom_coords = {
    # 1층
    '진로활동실': (260, 390, '1F'), '진로상담실': (290, 390, '1F'), '남교사휴게실': (315, 390, '1F'), '보건실': (345, 390, '1F'),
    '특수반': (405, 390, '1F'), '교장실': (450, 390, '1F'), '행정실': (490, 390, '1F'), '본관입구': (535, 390, '1F'),
    '1교무실': (610, 420, '1F'), '신발장1': (195, 345, '1F'), '신발장2': (715, 390, '1F'), '여교사휴게실': (735, 390, '1F'), 'wee 클래스': (765, 420, '1F'),
    '시청각실': (95, 205, '1F'), '준비실': (60, 250, '1F'), '문서고': (65, 390, '1F'), '학력향상실': (135, 345, '1F'),
    '학교운영위원회실': (170, 345, '1F'),

    # 1층 복도
    '복도-73': (95, 250, '1F'), '복도-74': (95, 280, '1F'), '복도-75': (95, 390, '1F'),
    '복도-76': (135, 390, '1F'), '복도-77': (170, 390, '1F'), '복도-78': (195, 390, '1F'),
    '복도-79': (220, 390, '1F'), '복도-80': (220, 420, '1F'), '복도-81': (260, 420, '1F'),
    '복도-82': (290, 420, '1F'), '복도-83': (315, 420, '1F'), '복도-84': (345, 420, '1F'),
    '복도-85': (375, 420, '1F'), '복도-86': (405, 420, '1F'), '복도-87': (450, 420, '1F'),
    '복도-88': (490, 420, '1F'), '복도-89': (535, 420, '1F'),
    '복도-91': (690, 420, '1F'), '복도-92': (715, 420, '1F'), '복도-93': (735, 420, '1F'),
    '복도-90': (610, 420, '1F'),

    # 1층 계단
    '계단11': (25, 280, '1F'), '계단12': (220, 345, '1F'), '계단13': (375, 345, '1F'),
    '계단14': (535, 455, '1F'), '계단15': (690, 345, '1F'),

    # 2층
    '1-1': (765, 390, '2F'), '1-2': (720, 390, '2F'), '1-3': (660, 390, '2F'), '1-4': (615, 390, '2F'),
    '1-5': (490, 390, '2F'), '1-6': (450, 390, '2F'), '1-7': (405, 390, '2F'), '1-8': (350, 390, '2F'),
    '1-9': (305, 390, '2F'), '1-10': (255, 390, '2F'), '방송실': (570, 390, '2F'), '제2교무실': (535, 390, '2F'),
    '1학년 홈베이스(1)': (175, 345, '2F'), '1학년 홈베이스(2)': (135, 345, '2F'), '화학생물실': (65, 390, '2F'),
    '학생활동실5': (65, 330, '2F'), '컴퓨터실': (65, 245, '2F'), 'ai융합실': (100, 165, '2F'),

    # 2층 복도
    '복도-1': (100, 245, '2F'), '복도-2': (100, 285, '2F'), '복도-3': (100, 330, '2F'),
    '복도-4': (100, 390, '2F'), '복도-5': (135, 390, '2F'), '복도-6': (175, 390, '2F'),
    '복도-7': (215, 390, '2F'), '복도-8': (215, 420, '2F'), '복도-9': (255, 420, '2F'),
    '복도-10': (305, 420, '2F'), '복도-11': (350, 420, '2F'), '복도-12': (375, 420, '2F'),
    '복도-13': (405, 420, '2F'), '복도-14': (450, 420, '2F'), '복도-15': (490, 420, '2F'), '복도-03': (535, 420, '2F'),
    '복도-16': (545, 420, '2F'), '복도-17': (570, 420, '2F'), '복도-18': (615, 420, '2F'),
    '복도-19': (660, 420, '2F'), '복도-20': (690, 420, '2F'), '복도-01': (720, 420, '2F'),
    '복도-02': (765, 420, '2F'),

    # 2층 계단
    '계단21': (30, 285, '2F'), '계단22': (215, 335, '2F'), '계단23': (375, 345, '2F'),
    '계단24': (545, 455, '2F'), '계단25': (690, 345, '2F'),

    # 3층
    '2-1': (715, 400, '3F'), '2-2': (650, 400, '3F'), '2-3': (605, 400, '3F'), '2-4': (570, 400, '3F'),
    '2-5': (480, 400, '3F'), '2-6': (435, 400, '3F'), '2-7': (400, 400, '3F'), '2-8': (335, 400, '3F'),
    '2-9': (290, 400, '3F'), '2-10': (245, 400, '3F'), '3교무실': (535, 400, '3F'), '4교무실': (763, 420, '3F'),
    '2학년 홈베이스(1)': (135, 370, '3F'), '2학년 홈베이스(2)': (180, 370, '3F'), '물리지구과학실': (75, 390, '3F'),
    '학생활동실4': (75, 345, '3F'), '학습실': (75, 255, '3F'), '도서열람실': (100, 185, '3F'),

    # 3층 복도
    '복도-21': (100, 255, '3F'), '복도-22': (100, 285, '3F'), '복도-23': (100, 345, '3F'),
    '복도-24': (100, 390, '3F'), '복도-25': (135, 390, '3F'), '복도-26': (180, 390, '3F'),
    '복도-27': (215, 390, '3F'), '복도-28': (215, 420, '3F'), '복도-29': (245, 420, '3F'),
    '복도-30': (290, 420, '3F'), '복도-31': (335, 420, '3F'), '복도-32': (380, 420, '3F'),
    '복도-33': (400, 420, '3F'), '복도-34': (435, 420, '3F'), '복도-35': (480, 420, '3F'),
    '복도-36': (530, 420, '3F'), '복도-37': (545, 420, '3F'), '복도-38': (570, 420, '3F'),
    '복도-39': (605, 420, '3F'), '복도-40': (650, 420, '3F'), '복도-41': (690, 420, '3F'),
    '복도-42': (715, 420, '3F'),

    # 3층 계단
    '계단31': (690, 350, '3F'), '계단32': (545, 460, '3F'), '계단33': (380, 350, '3F'),
    '계단34': (215, 335, '3F'), '계단35': (30, 285, '3F'),

    # 4층
    '3-1': (715, 400, '4F'), '3-2': (650, 400, '4F'), '3-3': (605, 400, '4F'), '3-4': (570, 400, '4F'),
    '3-5': (480, 400, '4F'), '3-6': (435, 400, '4F'), '3-7': (400, 400, '4F'), '3-8': (335, 400, '4F'),
    '3-9': (290, 400, '4F'), '3-10': (245, 400, '4F'), '학생활동실3': (535, 400, '4F'), '제5교무실': (763, 420, '4F'),
    '3학년 홈베이스(1)': (135, 370, '4F'), '3학년 홈베이스(2)': (180, 370, '4F'), '미술실': (75, 390, '4F'),
    '미술준비실': (75, 345, '4F'), '학생회실': (75, 255, '4F'), '학생활동실2': (100, 185, '4F'), '음악실': (100, 165, '4F'),

    # 4층 복도
    '복도-51': (100, 255, '4F'), '복도-52': (100, 285, '4F'), '복도-53': (100, 345, '4F'),
    '복도-54': (100, 390, '4F'), '복도-55': (135, 390, '4F'), '복도-56': (180, 390, '4F'),
    '복도-57': (215, 390, '4F'), '복도-58': (215, 420, '4F'), '복도-59': (245, 420, '4F'),
    '복도-60': (290, 420, '4F'), '복도-61': (335, 420, '4F'), '복도-62': (380, 420, '4F'),
    '복도-63': (400, 420, '4F'), '복도-64': (435, 420, '4F'), '복도-65': (480, 420, '4F'),
    '복도-66': (530, 420, '4F'), '복도-67': (545, 420, '4F'), '복도-68': (570, 420, '4F'),
    '복도-69': (605, 420, '4F'), '복도-70': (650, 420, '4F'), '복도-71': (690, 420, '4F'),
    '복도-72': (715, 420, '4F'),

    # 4층 계단
    '계단41': (690, 350, '4F'), '계단42': (545, 460, '4F'), '계단43': (380, 350, '4F'),
    '계단44': (215, 335, '4F'), '계단45': (30, 285, '4F')
}

edges_1f = [
    ('진로활동실', '복도-81'), ('진로상담실', '복도-82'), ('남교사휴게실', '복도-83'), ('보건실', '복도-84'),
    ('특수반', '복도-86'), ('교장실', '복도-87'), ('행정실', '복도-88'), ('본관입구', '복도-89'),
    ('신발장1', '복도-78'), ('여교사휴게실', '복도-93'), ('신발장2', '복도-92'),
    ('시청각실', '복도-73'), ('준비실', '복도-73'), ('문서고', '복도-75'), ('학력향상실', '복도-76'),
    ('학교운영위원회실', '복도-77'), ('wee 클래스', '복도-93'),
    ('복도-73', '복도-74'), ('복도-74', '복도-75'), ('복도-75', '복도-76'), ('복도-76', '복도-77'),
    ('복도-77', '복도-78'), ('복도-78', '복도-79'), ('복도-79', '복도-80'), ('복도-80', '복도-81'),
    ('복도-81', '복도-82'), ('복도-82', '복도-83'), ('복도-83', '복도-84'), ('복도-84', '복도-85'),
    ('복도-85', '복도-86'), ('복도-86', '복도-87'), ('복도-87', '복도-88'), ('복도-88', '복도-89'), ('복도-89', '1교무실'), ('1교무실', '복도-91'),
    ('복도-91', '복도-92'), ('복도-92', '복도-93'),
    ('복도-79', '복도-78'), ('복도-85', '복도-84'), ('복도-89', '복도-88'), ('복도-74', '복도-73'),
    ('계단11', '복도-74'), ('계단12', '복도-79'), ('계단13', '복도-85'), ('계단14', '복도-89'), ('계단15', '복도-91'),
]

edges_2f = [
    ('1-1', '복도-02'), ('1-2', '복도-01'), ('1-3', '복도-19'), ('1-4', '복도-18'),
    ('1-5', '복도-15'), ('1-6', '복도-14'), ('1-7', '복도-13'), ('1-8', '복도-11'),
    ('1-9', '복도-10'), ('1-10', '복도-9'), ('제2교무실', '복도-03'), ('방송실', '복도-17'),
    ('1학년 홈베이스(1)', '복도-6'), ('1학년 홈베이스(2)', '복도-5'), ('화학생물실', '복도-4'),
    ('학생활동실5', '복도-3'), ('컴퓨터실', '복도-1'), ('ai융합실', '복도-1'),
    ('복도-1', '복도-2'), ('복도-2', '복도-3'), ('복도-3', '복도-4'), ('복도-4', '복도-5'),
    ('복도-5', '복도-6'), ('복도-6', '복도-7'), ('복도-7', '복도-8'), ('복도-8', '복도-9'),
    ('복도-9', '복도-10'), ('복도-10', '복도-11'), ('복도-11', '복도-12'), ('복도-12', '복도-13'),
    ('복도-13', '복도-14'), ('복도-14', '복도-15'), ('복도-03', '복도-16'), ('복도-16', '복도-17'),
    ('복도-17', '복도-18'), ('복도-18', '복도-19'), ('복도-19', '복도-20'), ('복도-20', '복도-01'),
    ('복도-01', '복도-02'), ('복도-15', '복도-03'),
    ('계단21', '복도-2'), ('계단22', '복도-7'), ('계단23', '복도-12'), ('계단24', '복도-16'), ('계단25', '복도-20'),
]

edges_3f = [
    ('2-1', '복도-42'), ('2-2', '복도-40'), ('2-3', '복도-39'), ('2-4', '복도-38'),
    ('2-5', '복도-35'), ('2-6', '복도-34'), ('2-7', '복도-33'), ('2-8', '복도-31'),
    ('2-9', '복도-30'), ('2-10', '복도-29'), ('3교무실', '복도-37'), ('4교무실', '복도-42'),
    ('2학년 홈베이스(1)', '복도-25'), ('2학년 홈베이스(2)', '복도-26'), ('물리지구과학실', '복도-24'),
    ('학생활동실4', '복도-23'), ('학습실', '복도-21'), ('도서열람실', '복도-21'),
    ('복도-21', '복도-22'), ('복도-22', '복도-23'), ('복도-23', '복도-24'), ('복도-24', '복도-25'),
    ('복도-25', '복도-26'), ('복도-26', '복도-27'), ('복도-27', '복도-28'), ('복도-28', '복도-29'),
    ('복도-29', '복도-30'), ('복도-30', '복도-31'), ('복도-31', '복도-32'), ('복도-32', '복도-33'),
    ('복도-33', '복도-34'), ('복도-34', '복도-35'), ('복도-35', '복도-36'), ('복도-36', '복도-37'),
    ('복도-37', '복도-38'), ('복도-38', '복도-39'), ('복도-39', '복도-40'), ('복도-40', '복도-41'),
    ('복도-41', '복도-42'),
    ('계단31', '복도-41'), ('계단32', '복도-37'), ('계단33', '복도-32'), ('계단34', '복도-27'), ('계단35', '복도-22'),
]

edges_4f = [
    ('3-1', '복도-72'), ('3-2', '복도-70'), ('3-3', '복도-69'), ('3-4', '복도-68'),
    ('3-5', '복도-65'), ('3-6', '복도-64'), ('3-7', '복도-63'), ('3-8', '복도-61'),
    ('3-9', '복도-60'), ('3-10', '복도-59'), ('학생활동실3', '복도-66'), ('제5교무실', '복도-72'),
    ('3학년 홈베이스(1)', '복도-55'), ('3학년 홈베이스(2)', '복도-56'), ('미술실', '복도-54'),
    ('미술준비실', '복도-53'), ('학생회실', '복도-51'), ('학생활동실2', '복도-51'), ('음악실', '복도-51'),
    ('복도-51', '복도-52'), ('복도-52', '복도-53'), ('복도-53', '복도-54'), ('복도-54', '복도-55'),
    ('복도-55', '복도-56'), ('복도-56', '복도-57'), ('복도-57', '복도-58'), ('복도-58', '복도-59'),
    ('복도-59', '복도-60'), ('복도-60', '복도-61'), ('복도-61', '복도-62'), ('복도-62', '복도-63'),
    ('복도-63', '복도-64'), ('복도-64', '복도-65'), ('복도-65', '복도-66'), ('복도-66', '복도-67'),
    ('복도-67', '복도-68'), ('복도-68', '복도-69'), ('복도-69', '복도-70'), ('복도-70', '복도-71'),
    ('복도-71', '복도-72'),
    ('계단41', '복도-71'), ('계단42', '복도-67'), ('계단43', '복도-62'), ('계단44', '복도-57'), ('계단45', '복도-52'),
]

stairs_connections = {
    '계단11': '계단21', '계단21': '계단11',
    '계단12': '계단22', '계단22': '계단12',
    '계단13': '계단23', '계단23': '계단13',
    '계단14': '계단24', '계단24': '계단14',
    '계단15': '계단25', '계단25': '계단15',
    '계단21': '계단35', '계단35': '계단21',
    '계단22': '계단34', '계단34': '계단22',
    '계단23': '계단33', '계단33': '계단23',
    '계단24': '계단32', '계단32': '계단24',
    '계단25': '계단31', '계단31': '계단25',
    '계단31': '계단41', '계단41': '계단31',
    '계단32': '계단42', '계단42': '계단32',
    '계단33': '계단43', '계단43': '계단33',
    '계단34': '계단44', '계단44': '계단34',
    '계단35': '계단45', '계단45': '계단35',
}

floor_maps = {
    '1F': '1st floor.png',
    '2F': '2nd floor.png',
    '3F': '3rd floor.png',
    '4F': '4th floor.png',
}

# =========================
# 그래프 빌드 (원본 유지)
# =========================
G = nx.Graph()
G.add_edges_from(edges_1f + edges_2f + edges_3f + edges_4f)
for a, b in stairs_connections.items():
    G.add_edge(a, b)

# =========================
# 로직 함수 (원본 유지 + 비율계산만 수정)
# =========================
def find_path_with_floor_change(start_node, end_node):
    if start_node not in classroom_coords or end_node not in classroom_coords:
        return None
    try:
        return nx.shortest_path(G, source=start_node, target=end_node)
    except nx.NetworkXNoPath:
        return None
    except Exception:
        return None

def draw_path_on_floor(img: Image.Image, full_path, floor_key, line_width=5):
    """해당 층만 경로를 그려서 PIL 이미지 반환"""
    draw = ImageDraw.Draw(img)
    if not full_path:
        return img

    # 원본(800x600) 기준 → 현재 표시 크기 비율
    ratio_w = img.width / BASE_W
    ratio_h = img.height / BASE_H

    # 같은 층 구간 선
    nodes_on_floor = [n for n in full_path if n in classroom_coords and classroom_coords[n][2] == floor_key]
    for i in range(len(nodes_on_floor) - 1):
        n1, n2 = nodes_on_floor[i], nodes_on_floor[i + 1]
        if n1.startswith("계단") and n2.startswith("계단"):
            continue
        x1, y1, _ = classroom_coords[n1]
        x2, y2, _ = classroom_coords[n2]
        draw.line(
            (int(x1 * ratio_w), int(y1 * ratio_h), int(x2 * ratio_w), int(y2 * ratio_h)),
            fill='red', width=line_width
        )

    # 시작/도착/환승 마커
    for i, n in enumerate(full_path):
        if n not in classroom_coords:
            continue
        x0, y0, f = classroom_coords[n]
        if f != floor_key:
            continue
        x = int(x0 * ratio_w); y = int(y0 * ratio_h)
        if i == 0:
            draw.rectangle([x - 6, y - 6, x + 6, y + 6], fill="green")
        elif i == len(full_path) - 1:
            tri = [(x, y - 8), (x - 6, y + 6), (x + 6, y + 6)]
            draw.polygon(tri, fill="red")
        else:
            is_transition = False
            if i + 1 < len(full_path) and full_path[i + 1] in classroom_coords and classroom_coords[full_path[i + 1]][2] != f:
                is_transition = True
            if i - 1 >= 0 and full_path[i - 1] in classroom_coords and classroom_coords[full_path[i - 1]][2] != f:
                is_transition = True
            if is_transition and (n in stairs_connections or n in stairs_connections.values()):
                draw.ellipse([x - 10, y - 10, x + 10, y + 10], fill="blue", outline="darkblue", width=2)

    return img

# ===== 범례 이미지 생성 함수 추가 =====
def make_legend_image():
    w, h = 260, 160
    img = Image.new("RGBA", (w, h), "white")
    draw = ImageDraw.Draw(img)

    # 카드형 박스
    try:
        draw.rounded_rectangle([2, 2, w-2, h-2], radius=12, outline="#B0B0B0", width=2, fill="#FAFAFA")
    except Exception:
        # rounded_rectangle 미지원일 때 fallback
        draw.rectangle([2, 2, w-2, h-2], outline="#B0B0B0", width=2, fill="#FAFAFA")

    font_title = _load_korean_font(size=18)
    font_item = _load_korean_font(size=16)



    # 1) 출발지(초록 사각형)
    x, y = 18, 46
    draw.rectangle([x, y, x+16, y+16], fill="green")
    draw.text((x+28, y-4), "출발지점", font=font_item, fill="black")

    # 2) 층 이동(파란 원)
    y = 78
    draw.ellipse([x, y, x+18, y+18], fill="blue", outline="darkblue", width=2)
    draw.text((x+28, y-4), "층 이동 지점", font=font_item, fill="black")

    # 3) 도착지(빨간 삼각형)
    y = 112
    tri = [(x+9, y), (x, y+16), (x+18, y+16)]
    draw.polygon(tri, fill="red")
    draw.text((x+28, y-4), "도착지점", font=font_item, fill="black")

    return img

# =========================
# Streamlit UI
# =========================
st.title("울산여자고등학교 길찾기 시스템")

# ★ 층 상태 초기화 (자동 전환용)
if "current_floor" not in st.session_state:
    st.session_state["current_floor"] = "1F"
if "floor_radio" not in st.session_state:
    st.session_state["floor_radio"] = st.session_state["current_floor"]

classroom_only = sorted([k for k in classroom_coords if not k.startswith("복도") and not k.startswith("계단")])

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    start_default = classroom_only.index("1-1") if "1-1" in classroom_only else 0
    start = st.selectbox("출발지", options=classroom_only, index=start_default)
with col2:
    end_default = classroom_only.index("1-2") if "1-2" in classroom_only else 0
    end = st.selectbox("도착지", options=classroom_only, index=end_default)
with col3:
    if st.button("경로 표시", use_container_width=True):
        st.session_state["full_path"] = find_path_with_floor_change(start, end)
        # ★ 경로 표시 시, 출발지의 층으로 자동 전환
        start_floor = classroom_coords[start][2]
        st.session_state["current_floor"] = start_floor
        st.session_state["floor_radio"] = start_floor  # 라디오 즉시 반영

full_path = st.session_state.get("full_path", None)
if full_path is None:
    st.info("출발지/도착지를 선택하고 **경로 표시**를 눌러주세요.")
else:
    # ===== 층 이동 순서 표시 =====
    floor_seq = []
    for n in full_path:
        if n in classroom_coords:
            f = classroom_coords[n][2]
            if not floor_seq or floor_seq[-1] != f:
                floor_seq.append(f)
    st.success(f"층 이동: {' → '.join(floor_seq)}")

# ★ 라디오: 세션 상태 기반으로 표시/변경 동기화
floors = ['1F', '2F', '3F', '4F']
floor = st.radio(
    "현재 층 보기",
    options=floors,
    index=floors.index(st.session_state["floor_radio"]),
    horizontal=True,
    key="floor_radio",
)
# 라디오 변경 시 current_floor 동기화
st.session_state["current_floor"] = st.session_state["floor_radio"]
floor = st.session_state["floor_radio"]

map_path = floor_maps[floor]
try:
    base_img = Image.open(map_path).convert("RGBA")
except FileNotFoundError:
    st.error(f"지도 이미지 파일이 없습니다: {map_path}")
    st.stop()

# 화면 폭에 맞게 리사이즈 (표시용)
display_width = 1000
ratio = display_width / base_img.width
display_size = (display_width, int(base_img.height * ratio))
img = base_img.resize(display_size, Image.LANCZOS)

# 경로 오버레이
if full_path:
    img = draw_path_on_floor(img, full_path, floor)

# 1층 안내 문구 (회색 박스 제거, 외곽선만)
if floor == '1F':
    draw = ImageDraw.Draw(img)
    msg = "1층의 경우, 교무실을 통과하지 않고\n2층을 통해서 가주세요"
    font = _load_korean_font(size=20)

    try:
        bbox = draw.multiline_textbbox((0, 0), msg, font=font, align="right")
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except Exception:
        w, h = draw.textsize(msg, font=font)
    x = img.width - w - 20
    y = img.height - h - 20

    # 박스 없이 가독성만 확보 (흰색 외곽선)
    draw.multiline_text((x, y), msg, font=font, fill="black",
                        align="right", stroke_width=2, stroke_fill="white")

# ===== 지도 + 범례 나란히 배치 =====
col_map, col_legend = st.columns([4, 1])
with col_map:
    st.image(img, use_container_width=False)
with col_legend:
    legend_img = make_legend_image()
    st.image(legend_img, use_container_width=True)
