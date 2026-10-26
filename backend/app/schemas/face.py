from pydantic import BaseModel, Field, field_validator


class FaceSamplesRequest(BaseModel):
    samples: list[str] = Field(min_length=3, max_length=10)

    @field_validator("samples")
    @classmethod
    def validate_sample_sizes(cls, samples: list[str]) -> list[str]:
        if any(len(sample) > 1_500_000 for sample in samples):
            raise ValueError("Each face sample must be no larger than 1.5 MB when base64 encoded.")
        return samples


class FaceImageRequest(BaseModel):
    image: str = Field(min_length=1, max_length=1_500_000)
