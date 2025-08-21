import uvicorn
from fastapi import FastAPI, HTTPException
import numpy as np
import pandas as pd

data = pd.read_csv("BOOK.csv")
data.rename(columns={
    "ID": "id",
    "TITLE": "title",
    "AUTHOR": "author",
    "PUBLISHER": "publisher",
    "IMAGE": "image",
    "PRICE": "price",
    "PUBLISHED_AT": "publishedAt",
    "GENRE": "genre",
    "PAGE": "page",
    "INTRODUCTION": "introduction",
    "IS_DELETED": "isDeleted"
}, inplace=True)

tfidf_matrix = np.load("tfidf_matrix.npy")
cosine_sim = np.load("cosine_sim.npy")
print(tfidf_matrix.shape)
print(cosine_sim.shape)


def recommend(title, top_n=5):
    # 입력 책 인덱스 찾기
    idx = data[data['title'] == title].index[0]
    # 해당 책과 다른 책들의 유사도 벡터
    sim_scores = list(enumerate(cosine_sim[idx]))
    # 유사도 높은 순 정렬 (자기 자신 제외)
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n + 1]
    # 추천 책 인덱스 추출
    book_indices = [i[0] for i in sim_scores]
    return data[:].iloc[book_indices]


# 추천 함수 (책 ID 기반)
def recommend_by_id(book_id, top_n=5):
    # 입력 책 인덱스 찾기
    idx = data[data['id'] == book_id].index[0]  # 여기서 'ID' 컬럼 이름 확인
    print(idx)
    # 해당 책과 다른 책들의 유사도 벡터
    sim_scores = list(enumerate(cosine_sim[idx]))
    # 유사도 높은 순 정렬 (자기 자신 제외)
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n + 1]
    print(sim_scores)
    # 추천 책 인덱스 추출
    book_indices = [i[0] for i in sim_scores]
    print(book_indices)

    return data[:].iloc[book_indices]


app = FastAPI()


@app.get("/recommend")
def get_recommendation(title: str, top_n: int = 5):
    try:
        recommendations = recommend(title, top_n)
        return recommendations.to_dict(orient='records')
    except IndexError:
        raise HTTPException(status_code=404, detail="Book not found")


@app.get("/recommend_by_id")
def get_recommendation_by_id(book_id: int, top_n: int = 5):
    try:
        print(book_id)
        recommendations = recommend_by_id(book_id, top_n)
        return recommendations.to_dict(orient='records')
    except IndexError:
        raise HTTPException(status_code=404, detail="Book ID not found")


if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0",port=8848)

