import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from konlpy.tag import Okt

# 데이터 불러오기
data = pd.read_csv("BOOK.csv")

# 불용어 불러오기
with open("kor.txt", "r", encoding="utf-8") as f:
    stopwords = set([line.strip() for line in f.readlines() if line.strip()])

# 형태소 분석기 (명사만 추출 + 불용어 제거)
okt = Okt()


def tokenize(text):
    tokens = okt.nouns(str(text))
    return [word for word in tokens if word not in stopwords and len(word) > 1]


# 책 제목 + 설명 합치기
data['content'] = data['TITLE'].astype(str) + " " + data['INTRODUCTION'].astype(str)

# TF-IDF 벡터화
vectorizer = TfidfVectorizer(tokenizer=tokenize)
tfidf_matrix = vectorizer.fit_transform(data['content'])

# 코사인 유사도 계산
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
tfidf_dense = tfidf_matrix.toarray()
np.save("tfidf_matrix.npy", tfidf_dense)  # .npy 파일로 저장 (빠르고 용량 효율적)

# 2️⃣ 코사인 유사도 저장
np.save("cosine_sim.npy", cosine_sim)  # .npy 파일로 저장

# 3️⃣ 책 정보 저장 (ID, TITLE, INTRODUCTION)
data[['ID', 'TITLE', 'INTRODUCTION']].to_csv("book_data.csv", index=False, encoding="utf-8-sig")

print("✅ TF-IDF, 코사인 유사도, 책 데이터 저장 완료!")
# TF-IDF 단어(컬럼) 저장
feature_names = vectorizer.get_feature_names_out()
with open("tfidf_features.txt", "w", encoding="utf-8") as f:
    for word in feature_names:
        f.write(word + "\n")

print("✅ TF-IDF feature 단어 저장 완료!")

