from app.services.core.llm_service import LLMService
from app.services.core.retrieval_service import RetrievalService
from app.services.core.optimization_service import OptimizationService
from app.services.workflows.meal_suggestion_workflow import MealSuggestionWorkflowService
from app.services.workflows.meal_suggestion_workflow import MealSuggestionWorkflowService
from app.services.workflows.chatbot_workflow import ChatbotWorkflowService
from app.services.workflows.food_similarity_workflow import FoodSimilarityWorkflowService
from app.services.features.food_management_service import FoodManagementService

class Container:
    _instance = None

    def __init__(self):
        self.llm_service = LLMService()
        self.retrieval_service = RetrievalService(self.llm_service)
        self.optimization_service = OptimizationService()
        
        self.meal_workflow_service = MealSuggestionWorkflowService(
            self.llm_service,
            self.retrieval_service,
            self.optimization_service
        )
        
        self.chatbot_workflow_service = ChatbotWorkflowService(
            self.llm_service,
            self.retrieval_service,
            self.meal_workflow_service
        )
        
        self.food_similarity_service = FoodSimilarityWorkflowService(self.llm_service, self.retrieval_service, self.meal_workflow_service)
        
        self.food_management_service = FoodManagementService(self.retrieval_service)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

# Global instance
container = Container.get_instance()
