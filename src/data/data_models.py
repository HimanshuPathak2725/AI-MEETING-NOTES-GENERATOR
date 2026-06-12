"""Data models for the meeting notes generator."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass(frozen=False)
class Speaker:
    """Represents a speaker in a meeting."""
    id: str
    name: str
    speaking_time: int = 0  # seconds
    word_count: int = 0

    def to_dict(self) -> dict:
        """Serialize Speaker to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "speaking_time": self.speaking_time,
            "word_count": self.word_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Speaker":
        """Deserialize Speaker from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            speaking_time=data.get("speaking_time", 0),
            word_count=data.get("word_count", 0),
        )


@dataclass(frozen=False)
class TranscriptSegment:
    """A segment of transcribed speech."""
    start_time: int  # milliseconds
    end_time: int    # milliseconds
    speaker_id: str
    text: str
    confidence: float = 0.8

    def to_dict(self) -> dict:
        """Serialize TranscriptSegment to dictionary."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "speaker_id": self.speaker_id,
            "text": self.text,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TranscriptSegment":
        """Deserialize TranscriptSegment from dictionary."""
        return cls(
            start_time=data["start_time"],
            end_time=data["end_time"],
            speaker_id=data["speaker_id"],
            text=data["text"],
            confidence=data.get("confidence", 0.8),
        )


@dataclass(frozen=False)
class ActionItem:
    """A task or action item from the meeting."""
    description: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"

    def to_dict(self) -> dict:
        """Serialize ActionItem to dictionary."""
        return {
            "description": self.description,
            "assignee": self.assignee,
            "due_date": self.due_date,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ActionItem":
        """Deserialize ActionItem from dictionary."""
        return cls(
            description=data["description"],
            assignee=data.get("assignee"),
            due_date=data.get("due_date"),
            priority=data.get("priority", "medium"),
        )


@dataclass(frozen=False)
class MeetingResult:
    """Complete meeting analysis result."""
    title: str
    summary: str
    speakers: List[Speaker]
    segments: List[TranscriptSegment]
    action_items: List[ActionItem]
    language: str
    duration: int  # seconds
    processed_at: datetime
    
    @property
    def total_words(self) -> int:
        """Calculate total words in transcript."""
        return sum(len(segment.text.split()) for segment in self.segments)
    
    @property
    def avg_confidence(self) -> float:
        """Calculate average confidence score."""
        if not self.segments:
            return 0.0
        return sum(segment.confidence for segment in self.segments) / len(self.segments)
    
    @property
    def unique_speakers_count(self) -> int:
        """Get count of unique speakers."""
        return len(set(segment.speaker_id for segment in self.segments))

    def to_dict(self) -> dict:
        """Serialize MeetingResult to dictionary."""
        return {
            "title": self.title,
            "summary": self.summary,
            "speakers": [s.to_dict() for s in self.speakers],
            "segments": [seg.to_dict() for seg in self.segments],
            "action_items": [a.to_dict() for a in self.action_items],
            "language": self.language,
            "duration": self.duration,
            "processed_at": self.processed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MeetingResult":
        """Deserialize MeetingResult from dictionary."""
        return cls(
            title=data["title"],
            summary=data["summary"],
            speakers=[Speaker.from_dict(s) for s in data.get("speakers", [])],
            segments=[TranscriptSegment.from_dict(seg) for seg in data.get("segments", [])],
            action_items=[ActionItem.from_dict(a) for a in data.get("action_items", [])],
            language=data["language"],
            duration=data["duration"],
            processed_at=datetime.fromisoformat(data["processed_at"]),
        )