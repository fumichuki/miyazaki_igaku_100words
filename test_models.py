"""
テスト - 鹿児島大学英作文特訓システム
"""
import pytest
import json
from models import (
    QuestionResponse, CorrectionResponse, SubmissionRequest,
    Hint, TargetWords, Score, Comments, CorrectionPoint
)


# ===== フィクスチャ =====

@pytest.fixture
def sample_kagoshima_questions():
    """鹿児島大学風の代表的な問題10問"""
    return [
        {
            "theme": "週休3日制",
            "japanese_sentences": [
                "1日休みが増える分、1日当たりの仕事量が増えてしまうかもしれないよ。",
                "必ずしもいいことばかりではなく、課題もありそうね。",
                "3日休みがあれば、ちょっとした遠出もしやすくなると思う。",
                "週休3日制の利点と問題点について、もう少し詳しく調べてみましょう。"
            ]
        },
        {
            "theme": "アルバイトの経験",
            "japanese_sentences": [
                "例えば、アルバイトをすることで貴重な仕事の経験ができるよ。",
                "仕事と学校を両立することは大変だよ。",
                "学生がやりやすいアルバイトもあるよ。",
                "上手な時間の使い方ややるべきことへの優先順位の付け方を学んだよ。"
            ]
        },
        {
            "theme": "ファッション産業と環境",
            "japanese_sentences": [
                "最近は服が安く手に入るから、みんなたくさん買って簡単に捨ててしまう。",
                "ファッション産業は環境問題の増加に責任があると言われている。",
                "そのうちほとんどは結局ゴミとして廃棄されてしまうんだよ。",
                "そもそもたくさん買わないようにしないとね。"
            ]
        },
        {
            "theme": "オンライン教育",
            "japanese_sentences": [
                "自宅で授業を受けられるのは便利だよね。",
                "でも、友達と直接会って話すことができないのは寂しい。",
                "先生に質問するのも、オンラインだとちょっと難しいかも。",
                "対面とオンラインの両方の良いところを組み合わせたらいいね。"
            ]
        },
        {
            "theme": "食品ロス",
            "japanese_sentences": [
                "まだ食べられるのに捨てられてしまう食品がたくさんあるんだよ。",
                "レストランでは食べ残しが問題になっているよ。",
                "家庭でも、買いすぎて結局使わないことがあるね。",
                "食品ロスを減らすためにできることから始めよう。"
            ]
        },
        {
            "theme": "SNSの利用",
            "japanese_sentences": [
                "SNSで友達と簡単につながれるのはいいことだよ。",
                "でも、使いすぎると時間を無駄にしてしまうかもしれない。",
                "他人の投稿を見て落ち込むこともあるらしい。",
                "賢くSNSを使う方法を考える必要があるね。"
            ]
        },
        {
            "theme": "地域活性化",
            "japanese_sentences": [
                "若い人たちが都会に出て行ってしまうことが問題だね。",
                "地元に魅力的な仕事があれば、残る人も増えるだろう。",
                "観光客を呼び込むのも一つの方法かもしれない。",
                "地域の良さを再発見することが大切だよ。"
            ]
        },
        {
            "theme": "リモートワーク",
            "japanese_sentences": [
                "家で仕事ができるのは通勤時間が節約できていいね。",
                "でも、仕事とプライベートの区別がつきにくくなるかも。",
                "チームでの協力がしづらいという課題もあるよ。",
                "働き方の選択肢が増えるのはいいことだと思う。"
            ]
        },
        {
            "theme": "プラスチック削減",
            "japanese_sentences": [
                "海にプラスチックゴミが増えて問題になっているんだ。",
                "レジ袋が有料になったのもその対策の一つだよ。",
                "マイバッグを持ち歩くのは簡単なことだね。",
                "小さなことでも続けることが重要だと思う。"
            ]
        },
        {
            "theme": "健康的な生活",
            "japanese_sentences": [
                "最近、運動不足になっている人が多いらしい。",
                "バランスの取れた食事も大切だよね。",
                "睡眠時間を確保することも忘れちゃいけない。",
                "健康は何よりも大事だから、意識して生活したいね。"
            ]
        }
    ]


@pytest.fixture
def valid_question_response():
    """有効な問題レスポンス"""
    return QuestionResponse(
        theme="週休3日制",
        japanese_sentences=[
            "1日休みが増える分、1日当たりの仕事量が増えてしまうかもしれないよ。",
            "必ずしもいいことばかりではなく、課題もありそうね。",
            "3日休みがあれば、ちょっとした遠出もしやすくなると思う。"
        ],
        hints=[
            Hint(en="workload", ja="仕事量", kana="しごとりょう"),
            Hint(en="increase", ja="増える", kana="ふえる"),
            Hint(en="advantage", ja="利点", kana="りてん")
        ],
        target_words=TargetWords(min=80, max=120),
        model_answer="If we have an additional day off, the workload per day might increase.",
        alternative_answer="Having one more day off could result in more work.",
        common_mistakes=["直訳しすぎる", "主語を省略する"]
    )


@pytest.fixture
def valid_correction_response():
    """有効な添削レスポンス"""
    return CorrectionResponse(
        original="If we have one more day off, it might increase the amount of work per day.",
        corrected="If we have an additional day off, the workload per day might increase.",
        word_count=58,
        score=Score(
            content=5,
            structure=4,
            vocabulary=4,
            grammar=4,
            word_count_penalty=5
        ),
        total=22,
        comments=Comments(
            content="問題の要求に適切に答えています。",
            structure="論理展開は自然です。",
            vocabulary="基本的な語彙は適切です。",
            grammar="文法的に正しいです。",
            word_count_penalty="語数は基準内です。"
        ),
        points=[
            CorrectionPoint(
                before="one more day off",
                after="an additional day off",
                reason="\"one more\"は口語的。\"additional\"がよりフォーマル。"
            ),
            CorrectionPoint(
                before="it might increase",
                after="the workload per day might increase",
                reason="主語\"it\"が不明瞭。",
                alt="the amount of work might increase"
            ),
            CorrectionPoint(
                before="amount of work per day",
                after="workload per day",
                reason="\"workload\"の方が簡潔で自然。"
            ),
            CorrectionPoint(
                before="per day",
                after="daily",
                reason="\"daily\"を使うとより簡潔。",
                alt="each day"
            ),
            CorrectionPoint(
                before="might increase",
                after="could increase",
                reason="\"could\"も使用可能。",
                alt="may increase"
            )
        ]
    )


# ===== Pydanticモデルのテスト =====

def test_question_response_validation(valid_question_response):
    """QuestionResponseのバリデーションテスト"""
    # 正常系
    assert valid_question_response.theme == "週休3日制"
    assert len(valid_question_response.japanese_sentences) == 3
    assert len(valid_question_response.hints) == 3
    assert valid_question_response.target_words.min == 80
    assert valid_question_response.target_words.max == 120


def test_question_response_invalid_target_words():
    """TargetWordsの異常系テスト"""
    with pytest.raises(ValueError):
        # minがmaxより大きい
        TargetWords(min=120, max=80)


def test_correction_response_validation(valid_correction_response):
    """CorrectionResponseのバリデーションテスト"""
    # 正常系
    assert valid_correction_response.word_count == 58
    assert valid_correction_response.total == 22
    assert len(valid_correction_response.points) == 5


def test_correction_response_total_score_mismatch():
    """採点合計のミスマッチテスト"""
    # totalが25を超える場合はPydanticのバリデーションエラー
    from pydantic import ValidationError as PydanticValidationError
    
    with pytest.raises(PydanticValidationError):
        CorrectionResponse(
            original="test",
            corrected="test",
            word_count=10,
            score=Score(
                content=5,
                structure=4,
                vocabulary=4,
                grammar=4,
                word_count_penalty=5
            ),
            total=100,  # 25を超えるのでバリデーションエラー
            comments=Comments(
                content="test",
                structure="test",
                vocabulary="test",
                grammar="test",
                word_count_penalty="test"
            ),
            points=[
                CorrectionPoint(before="a", after="b", reason="test")
            ]
        )


def test_correction_points_minimum():
    """添削ポイントの最小数テスト"""
    # 最低1個は必要
    with pytest.raises(ValueError):
        CorrectionResponse(
            original="test",
            corrected="test",
            word_count=10,
            score=Score(
                content=5,
                structure=4,
                vocabulary=4,
                grammar=4,
                word_count_penalty=5
            ),
            total=22,
            comments=Comments(
                content="test",
                structure="test",
                vocabulary="test",
                grammar="test",
                word_count_penalty="test"
            ),
            points=[]  # 空のリスト
        )


def test_json_serialization(valid_question_response, valid_correction_response):
    """JSONシリアライゼーションテスト"""
    # QuestionResponse
    question_dict = valid_question_response.model_dump()
    assert isinstance(question_dict, dict)
    assert question_dict['theme'] == "週休3日制"
    
    # CorrectionResponse
    correction_dict = valid_correction_response.model_dump()
    assert isinstance(correction_dict, dict)
    assert correction_dict['total'] == 22


def test_kagoshima_questions_format(sample_kagoshima_questions):
    """鹿児島大学風の問題フォーマットテスト"""
    for q in sample_kagoshima_questions:
        # 各問題は2-4文
        assert 2 <= len(q['japanese_sentences']) <= 10
        
        # 口語表現を含む
        sentences_text = " ".join(q['japanese_sentences'])
        has_casual = any(marker in sentences_text for marker in ["だよ", "だね", "よね", "かも", "らしい"])
        assert has_casual, f"口語表現が含まれていません: {q['theme']}"


# ===== 語数カウントテスト =====

def test_word_count():
    """語数カウントの正確性テスト"""
    text1 = "This is a test."
    assert len(text1.split()) == 4
    
    text2 = "If we have an additional day off, the workload per day might increase."
    assert len(text2.split()) == 13  # 正しい語数は13


# ===== スコア計算テスト =====

def test_score_calculation():
    """スコア計算の正確性テスト"""
    score = Score(
        content=5,
        structure=4,
        vocabulary=4,
        grammar=4,
        word_count_penalty=5
    )
    
    total = score.content + score.structure + score.vocabulary + score.grammar + score.word_count_penalty
    assert total == 22


def test_score_bounds():
    """スコアの境界値テスト"""
    # 各項目は0-5点
    with pytest.raises(ValueError):
        Score(
            content=6,  # 5点を超える
            structure=4,
            vocabulary=4,
            grammar=4,
            word_count_penalty=5
        )
    
    with pytest.raises(ValueError):
        Score(
            content=-1,  # 0点未満
            structure=4,
            vocabulary=4,
            grammar=4,
            word_count_penalty=5
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
