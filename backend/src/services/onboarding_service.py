"""Onboarding service for providing onboarding materials and best practices."""

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.collection import Collection
from src.models.faq import FAQ
from src.schemas.onboarding import BestPracticesResponse, OnboardingResponse, OnboardingSection


class OnboardingService:
    """Service for handling onboarding operations."""

    @staticmethod
    def get_onboarding_materials(db: Session) -> OnboardingResponse:
        """
        Get onboarding materials for new users.

        Args:
            db: Database session

        Returns:
            OnboardingResponse: Onboarding materials
        """
        # Get featured collections
        featured_collections = (
            db.query(Collection)
            .filter(Collection.is_featured == True)
            .order_by(Collection.display_order, Collection.created_at.desc())
            .limit(5)
            .all()
        )

        # Get FAQs (getting_started category)
        getting_started_faqs = (
            db.query(FAQ)
            .filter(
                FAQ.is_active == True,
                FAQ.category == "getting_started",
            )
            .order_by(FAQ.display_order, FAQ.created_at.desc())
            .limit(5)
            .all()
        )

        # Build onboarding sections
        getting_started_sections = [
            OnboardingSection(
                title="Welcome to PromptShare",
                content="PromptShare is an internal platform for sharing and discovering effective prompts for AI tools like GitHub Copilot, O365 Copilot, Cursor, and Claude.",
                order=1,
            ),
            OnboardingSection(
                title="Getting Started",
                content="Browse prompts by category, search by keyword, or explore featured collections. Click on any prompt to view details and copy it with one click.",
                order=2,
            ),
            OnboardingSection(
                title="Contributing",
                content="Share your own prompts by clicking 'Create Prompt'. Include clear descriptions, usage tips, and relevant categories to help others discover your work.",
                order=3,
            ),
            OnboardingSection(
                title="Engagement",
                content="Rate prompts, leave comments, and upvote helpful prompts. Follow categories to receive notifications about new prompts in your areas of interest.",
                order=4,
            ),
        ]

        # Quick tips
        quick_tips = [
            "Use specific, clear language in your prompts",
            "Include context about when and how to use the prompt",
            "Tag prompts with appropriate platforms and categories",
            "Review and rate prompts you've used successfully",
            "Follow categories relevant to your work",
        ]

        # Convert collections and FAQs to response schemas
        from src.schemas.collection import CollectionResponse
        from src.schemas.faq import FAQResponse

        collection_responses = [
            CollectionResponse.model_validate(c) for c in featured_collections
        ]
        faq_responses = [
            FAQResponse.model_validate(f) for f in getting_started_faqs
        ]

        return OnboardingResponse(
            welcome_message="Welcome to PromptShare! This platform helps you discover and share effective prompts for AI tools.",
            getting_started=getting_started_sections,
            featured_collections=collection_responses,
            quick_tips=quick_tips,
            faqs=faq_responses,
        )

    @staticmethod
    def get_best_practices(db: Session) -> BestPracticesResponse:
        """
        Get best practices for using prompts.

        Args:
            db: Database session

        Returns:
            BestPracticesResponse: Best practices information
        """
        general_tips = [
            "Be specific about what you want the AI to do",
            "Provide context and background information",
            "Use clear, concise language",
            "Break complex tasks into smaller prompts",
            "Iterate and refine prompts based on results",
            "Test prompts before sharing them",
        ]

        platform_specific_tips = {
            "github_copilot": [
                "Use comments to guide Copilot's suggestions",
                "Provide function signatures and docstrings",
                "Break code into logical sections",
            ],
            "o365_copilot": [
                "Be specific about document types and formats",
                "Include examples of desired output",
                "Specify tone and style preferences",
            ],
            "cursor": [
                "Use natural language to describe code changes",
                "Reference existing code patterns in your codebase",
                "Be explicit about file locations and imports",
            ],
            "claude": [
                "Use clear instructions and examples",
                "Specify output format when needed",
                "Provide context about the task domain",
            ],
        }

        common_mistakes = [
            "Being too vague or ambiguous",
            "Not providing enough context",
            "Using overly complex language",
            "Forgetting to test prompts before sharing",
            "Not updating prompts based on feedback",
        ]

        resources = [
            {
                "title": "Prompt Engineering Guide",
                "url": "/docs/prompt-engineering",
                "description": "Learn the fundamentals of prompt engineering",
            },
            {
                "title": "API Documentation",
                "url": "/api/docs",
                "description": "Explore the PromptShare API",
            },
        ]

        return BestPracticesResponse(
            general_tips=general_tips,
            platform_specific_tips=platform_specific_tips,
            common_mistakes=common_mistakes,
            resources=resources,
        )

