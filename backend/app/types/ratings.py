from pydantic import BaseModel, ConfigDict, Field


class RatingRow(BaseModel):
    """数据库行映射"""
    id: int
    event_id: int
    user_id: int
    score: int
    created_at: str
    updated_at: str


class EventRatingSummary(BaseModel):
    """返回给前端的评分统计"""
    average: float | None = Field(default=None, description="平均分，保留1位小数")
    count: int = Field(default=0, description="评分总人数")
    my_score: int | None = Field(default=None, alias="myScore", description="当前用户打的分数")


class RateEventRequest(BaseModel):
    """前端提交评分的请求体"""
    model_config = ConfigDict(extra="forbid")
    score: int = Field(..., ge=1, le=5, description="分数必须在1到5之间")