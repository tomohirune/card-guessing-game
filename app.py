import streamlit as st
import random
import uuid
from datetime import datetime

# =========================================================
# Zoom通話しながら遊ぶカード推理ゲーム / Streamlit版
# ---------------------------------------------------------
# 実行方法:
# 1. このファイルを app.py という名前で保存
# 2. ターミナルで以下を実行
#    pip install streamlit
#    streamlit run app.py
# 3. 表示されたURLをプレイヤーA/Bに共有
# =========================================================

st.set_page_config(
    page_title="Card Guessing Game",
    page_icon="🃏",
    layout="centered",
)

# -----------------------------
# 基本設定
# -----------------------------
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
INITIAL_HAND_SIZE = 8
DRAW_ON_CORRECT = 2


def build_deck():
    """52枚のトランプを作成する。"""
    return [f"{suit}{rank}" for suit in SUITS for rank in RANKS]


def new_room():
    """新しいゲームルームを作成する。"""
    room_id = str(uuid.uuid4())[:8]
    deck = build_deck()
    random.shuffle(deck)

    password_a = str(random.randint(1000, 9999))
    password_b = str(random.randint(1000, 9999))

    st.session_state.rooms[room_id] = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passwords": {
            "A": password_a,
            "B": password_b,
        },
        "hands": {
            "A": deck[:INITIAL_HAND_SIZE],
            "B": deck[INITIAL_HAND_SIZE:INITIAL_HAND_SIZE * 2],
        },
        "draw_pile": deck[INITIAL_HAND_SIZE * 2:],
        "turn": "A",
        "skip": {
            "A": False,
            "B": False,
        },
        "game_over": False,
        "winner": None,
        "history": [
            f"ゲーム開始。プレイヤーA・Bにそれぞれ{INITIAL_HAND_SIZE}枚配りました。"
        ],
    }
    return room_id, password_a, password_b


def get_opponent(player):
    return "B" if player == "A" else "A"


def card_sort_key(card):
    suit = card[0]
    rank = card[1:]
    return (SUITS.index(suit), RANKS.index(rank))


def next_turn(room):
    """ターンを相手に渡す。"""
    room["turn"] = get_opponent(room["turn"])


def draw_cards(room, player, count):
    """山札から指定枚数カードを引く。山札が足りない場合はある分だけ引く。"""
    drawn = []
    for _ in range(count):
        if room["draw_pile"]:
            drawn.append(room["draw_pile"].pop(0))
    room["hands"][player].extend(drawn)
    return drawn


def check_winner(room):
    """どちらかの手札が0枚になったら勝敗を決める。"""
    if len(room["hands"]["A"]) == 0:
        room["game_over"] = True
        room["winner"] = "B"
    elif len(room["hands"]["B"]) == 0:
        room["game_over"] = True
        room["winner"] = "A"


def reset_room(room_id):
    """同じルームIDでゲームを初期化する。"""
    old_passwords = st.session_state.rooms[room_id]["passwords"]
    deck = build_deck()
    random.shuffle(deck)

    st.session_state.rooms[room_id] = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passwords": old_passwords,
        "hands": {
            "A": deck[:INITIAL_HAND_SIZE],
            "B": deck[INITIAL_HAND_SIZE:INITIAL_HAND_SIZE * 2],
        },
        "draw_pile": deck[INITIAL_HAND_SIZE * 2:],
        "turn": "A",
        "skip": {
            "A": False,
            "B": False,
        },
        "game_over": False,
        "winner": None,
        "history": [
            f"ゲームをリセットしました。プレイヤーA・Bにそれぞれ{INITIAL_HAND_SIZE}枚配りました。"
        ],
    }


# -----------------------------
# セッション初期化
# -----------------------------
if "rooms" not in st.session_state:
    st.session_state.rooms = {}

if "joined_room_id" not in st.session_state:
    st.session_state.joined_room_id = ""

if "joined_player" not in st.session_state:
    st.session_state.joined_player = ""

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


# -----------------------------
# サイドバー：ルーム作成・参加
# -----------------------------
st.sidebar.title("🃏 ゲーム設定")

st.sidebar.subheader("1. ルーム作成")
if st.sidebar.button("新しいルームを作成"):
    room_id, password_a, password_b = new_room()
    st.session_state.joined_room_id = room_id
    st.session_state.joined_player = "A"
    st.session_state.authenticated = True
    st.sidebar.success("ルームを作成しました。")
    st.sidebar.info(f"ルームID: {room_id}\n\nAの合言葉: {password_a}\n\nBの合言葉: {password_b}")

st.sidebar.divider()

st.sidebar.subheader("2. ルーム参加")
input_room_id = st.sidebar.text_input("ルームID", value=st.session_state.joined_room_id)
input_player = st.sidebar.radio("参加するプレイヤー", ["A", "B"], horizontal=True)
input_password = st.sidebar.text_input("合言葉", type="password")

if st.sidebar.button("参加する"):
    if input_room_id not in st.session_state.rooms:
        st.sidebar.error("そのルームIDは見つかりません。")
    else:
        room = st.session_state.rooms[input_room_id]
        if input_password == room["passwords"][input_player]:
            st.session_state.joined_room_id = input_room_id
            st.session_state.joined_player = input_player
            st.session_state.authenticated = True
            st.sidebar.success(f"プレイヤー{input_player}として参加しました。")
        else:
            st.session_state.authenticated = False
            st.sidebar.error("合言葉が違います。")

st.sidebar.divider()
st.sidebar.caption("Zoomで会話しながら、それぞれが自分の画面を開いて遊ぶ想定です。")


# -----------------------------
# メイン画面
# -----------------------------
st.title("🃏 カード推理ゲーム")
st.caption("Zoom通話をしながら、相手のカードを推理して当てるゲームです。")

if not st.session_state.authenticated:
    st.info("左のサイドバーから、新しいルームを作成するか、ルームIDと合言葉を入力して参加してください。")

    with st.expander("遊び方"):
        st.markdown(
            f"""
            - プレイヤーA・Bに、それぞれ最初に **{INITIAL_HAND_SIZE}枚** 配られます。
            - 自分の手札だけが画面に表示されます。
            - 相手の手札は見えません。相手の残り枚数だけ表示されます。
            - Zoomで質問しながら、相手のカードを推理します。
            - 宣言が当たると、相手の手札からそのカードが消え、自分は山札から **{DRAW_ON_CORRECT}枚** 引きます。
            - 宣言が外れると、自分の次のターンがスキップされます。
            - 相手の手札を0枚にしたら勝利です。
            """
        )
    st.stop()

room_id = st.session_state.joined_room_id
player = st.session_state.joined_player

if room_id not in st.session_state.rooms:
    st.error("ルームが見つかりません。もう一度参加してください。")
    st.stop()

room = st.session_state.rooms[room_id]
opponent = get_opponent(player)

# -----------------------------
# 状態表示
# -----------------------------
st.subheader(f"あなたはプレイヤー{player}です")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("現在のターン", f"プレイヤー{room['turn']}")
with col2:
    st.metric("相手の残り枚数", len(room["hands"][opponent]))
with col3:
    st.metric("山札", len(room["draw_pile"]))

if room["game_over"]:
    if room["winner"] == player:
        st.success("🎉 あなたの勝利です！")
    else:
        st.error(f"プレイヤー{room['winner']}の勝利です。")

    if st.button("同じルームでもう一度遊ぶ"):
        reset_room(room_id)
        st.rerun()

    st.stop()

# -----------------------------
# 手札表示
# -----------------------------
st.markdown("### あなたの手札")
my_hand = sorted(room["hands"][player], key=card_sort_key)

if my_hand:
    st.write("　".join([f"`{card}`" for card in my_hand]))
else:
    st.write("手札はありません。")

st.markdown("### 相手の情報")
st.write(f"プレイヤー{opponent}の手札は **{len(room['hands'][opponent])}枚** です。")
st.write("相手のカード内容は表示されません。")

# -----------------------------
# ターン処理
# -----------------------------
st.divider()
st.markdown("## 行動")

if room["turn"] != player:
    st.info(f"現在はプレイヤー{room['turn']}のターンです。Zoomで相手の行動を待ってください。")
    if st.button("画面を更新"):
        st.rerun()
else:
    if room["skip"][player]:
        st.warning("前回の宣言ミスにより、このターンはスキップです。")
        if st.button("スキップして相手にターンを渡す"):
            room["history"].append(f"プレイヤー{player}はターンスキップしました。")
            room["skip"][player] = False
            next_turn(room)
            st.rerun()
    else:
        action = st.radio("行動を選んでください", ["質問した", "宣言する"], horizontal=True)

        if action == "質問した":
            st.caption("質問と回答はZoomで行います。ここでは記録だけ残せます。")
            question = st.text_input("質問内容（任意）", placeholder="例：ハートは何枚ありますか？")
            answer = st.text_input("相手の回答（任意）", placeholder="例：2枚です")

            if st.button("質問を記録してターン終了"):
                if question or answer:
                    room["history"].append(
                        f"プレイヤー{player}が質問: {question or '未入力'} / 回答: {answer or '未入力'}"
                    )
                else:
                    room["history"].append(f"プレイヤー{player}が質問をしました。")
                next_turn(room)
                st.rerun()

        if action == "宣言する":
            st.caption("相手が持っていると思うカードを1枚選んで宣言します。")

            guess_suit = st.selectbox("マーク", SUITS, horizontal=False)
            guess_rank = st.selectbox("数字", RANKS, horizontal=False)
            guess_card = f"{guess_suit}{guess_rank}"

            st.write(f"宣言するカード: **{guess_card}**")

            if st.button("このカードで宣言する"):
                opponent_hand = room["hands"][opponent]

                if guess_card in opponent_hand:
                    opponent_hand.remove(guess_card)
                    drawn_cards = draw_cards(room, player, DRAW_ON_CORRECT)

                    if drawn_cards:
                        room["history"].append(
                            f"プレイヤー{player}が {guess_card} を宣言して正解。プレイヤー{opponent}の手札から除外し、{len(drawn_cards)}枚引きました。"
                        )
                    else:
                        room["history"].append(
                            f"プレイヤー{player}が {guess_card} を宣言して正解。プレイヤー{opponent}の手札から除外しました。山札がないためカードは引けませんでした。"
                        )

                    check_winner(room)
                    if not room["game_over"]:
                        next_turn(room)

                    st.success(f"正解！ {guess_card} は相手の手札にありました。")
                    st.rerun()
                else:
                    room["history"].append(
                        f"プレイヤー{player}が {guess_card} を宣言しましたが、不正解。次のプレイヤー{player}のターンはスキップになります。"
                    )
                    room["skip"][player] = True
                    next_turn(room)
                    st.error(f"不正解。{guess_card} は相手の手札にありませんでした。")
                    st.rerun()

# -----------------------------
# 履歴表示
# -----------------------------
st.divider()
st.markdown("## ゲーム履歴")

for item in reversed(room["history"][-20:]):
    st.write("- " + item)

# -----------------------------
# 管理用情報
# -----------------------------
with st.expander("ルーム情報"):
    st.write(f"ルームID: `{room_id}`")
    st.write(f"作成日時: {room['created_at']}")
    st.write("プレイヤーA/Bの合言葉は、ルーム作成者のサイドバーに表示されます。")
    st.warning("実際に使う場合は、自分の手札画面をZoomで画面共有しないように注意してください。")
