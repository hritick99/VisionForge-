"""
Complete AI Vision Image Analyzer
Supports: GPT-4o, Claude Sonnet 4.5, and Gemini Vision
"""

import os
import base64
from pathlib import Path
from typing import Literal, Optional
import json

# Install required packages:
# pip install openai anthropic google-generativeai pillow

class VisionAnalyzer:
    """Universal image analyzer supporting multiple AI vision models"""
    
    def __init__(
        self,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        google_key: Optional[str] = None
    ):
        """
        Initialize with API keys
        If None, will try to read from environment variables
        """
        self.openai_key = openai_key or os.getenv('OPENAI_API_KEY')
        self.anthropic_key = anthropic_key or os.getenv('ANTHROPIC_API_KEY')
        self.google_key = google_key or os.getenv('GOOGLE_API_KEY')
        
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def get_media_type(self, image_path: str) -> str:
        """Get media type from file extension"""
        ext = Path(image_path).suffix.lower()
        media_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return media_types.get(ext, 'image/jpeg')
    
    def analyze_with_gpt4o(
        self,
        image_path: str,
        custom_prompt: Optional[str] = None,
        analysis_type: str = "detailed"
    ) -> str:
        
        try:
            from openai import OpenAI
        except ImportError:
            return "Error: Please install openai package: pip install openai"
        
        if not self.openai_key:
            return "Error: OpenAI API key not found. Set OPENAI_API_KEY environment variable."
        
        prompts = {
            "detailed": """Analyze this image in comprehensive detail:
1. Main subjects, objects, and people
2. Scene setting and environment
3. Colors, lighting, shadows, and composition
4. Mood, atmosphere, and emotions conveyed
5. Any visible text or signs
6. Quality, style, and artistic elements
7. Context and possible purpose
8. Notable or unique details""",
            
            "story": """Create a rich, engaging story based on this image:
- Describe what's happening right now
- Imagine the backstory and context
- Develop the characters or subjects
- Explore emotions and relationships
- Predict what might happen next
- Make it vivid and compelling!""",
            
            "technical": """Provide expert technical analysis:
- Composition techniques (rule of thirds, leading lines, etc.)
- Lighting setup and quality (natural/artificial, direction, softness)
- Color grading and palette
- Depth of field and focus points
- Camera settings estimation (aperture, shutter, ISO if applicable)
- Post-processing techniques visible
- Image quality and resolution
- Professional photography principles applied""",
            
            "creative": """Deep creative analysis:
- Artistic style and influences
- Symbolism and metaphors
- Cultural or historical context
- Emotional and psychological impact
- Narrative and storytelling elements
- Potential interpretations
- How it relates to art movements or genres"""
        }
        
        prompt = custom_prompt or prompts.get(analysis_type, prompts["detailed"])
        
        try:
            client = OpenAI(api_key=self.openai_key)
            base64_image = self.encode_image(image_path)
            media_type = self.get_media_type(image_path)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error with GPT-4o: {str(e)}"
    
    def analyze_with_claude(
        self,
        image_path: str,
        custom_prompt: Optional[str] = None,
        analysis_type: str = "detailed"
    ) -> str:
        """
        Analyze image using Claude Sonnet 4.5
        
        Args:
            image_path: Path to image file
            custom_prompt: Custom prompt (overrides analysis_type)
            analysis_type: 'detailed', 'story', 'technical', 'creative'
        """
        try:
            import anthropic
        except ImportError:
            return "Error: Please install anthropic package: pip install anthropic"
        
        if not self.anthropic_key:
            return "Error: Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable."
        
        prompts = {
            "detailed": "Analyze this image in extreme detail. Describe everything you see, the mood, composition, colors, lighting, subjects, context, and any interesting details.",
            "story": "Look at this image and write a captivating story about it. Include vivid descriptions, character backgrounds, emotions, and what might happen next.",
            "technical": "Provide a professional technical analysis of this image covering composition, lighting, color theory, photography techniques, and quality assessment.",
            "creative": "Analyze this image creatively. Discuss artistic style, symbolism, emotional impact, cultural context, and deeper meanings."
        }
        
        prompt = custom_prompt or prompts.get(analysis_type, prompts["detailed"])
        
        try:
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            media_type = self.get_media_type(image_path)
            
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )
            
            return message.content[0].text
            
        except Exception as e:
            return f"Error with Claude: {str(e)}"
    
    def analyze_with_gemini(
        self,
        image_path: str,
        custom_prompt: Optional[str] = None,
        analysis_type: str = "detailed"
    ) -> str:
        """
        Analyze image using Google Gemini Vision
        
        Args:
            image_path: Path to image file
            custom_prompt: Custom prompt
            analysis_type: 'detailed', 'story', 'technical', 'creative'
        """
        try:
            import google.generativeai as genai
            from PIL import Image
        except ImportError:
            return "Error: Please install: pip install google-generativeai pillow"
        
        if not self.google_key:
            return "Error: Google API key not found. Set GOOGLE_API_KEY environment variable."
        
        prompts = {
            "detailed": "Analyze this image thoroughly and describe everything you observe.",
            "story": "Create an engaging story based on this image.",
            "technical": "Provide technical analysis of this image's composition and quality.",
            "creative": "Analyze this image from an artistic and creative perspective."
        }
        
        prompt = custom_prompt or prompts.get(analysis_type, prompts["detailed"])
        
        try:
            genai.configure(api_key=self.google_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            img = Image.open(image_path)
            response = model.generate_content([prompt, img])
            
            return response.text
            
        except Exception as e:
            return f"Error with Gemini: {str(e)}"
    
    def compare_models(self, image_path: str, analysis_type: str = "detailed") -> dict:
        """
        Run the same image through all available models and compare results
        
        Returns:
            Dictionary with results from each model
        """
        results = {}
        
        if self.openai_key:
            print("Analyzing with GPT-4o...")
            results['gpt4o'] = self.analyze_with_gpt4o(image_path, analysis_type=analysis_type)
        
        if self.anthropic_key:
            print("Analyzing with Claude...")
            results['claude'] = self.analyze_with_claude(image_path, analysis_type=analysis_type)
        
        if self.google_key:
            print("Analyzing with Gemini...")
            results['gemini'] = self.analyze_with_gemini(image_path, analysis_type=analysis_type)
        
        return results
    
    def save_results(self, results: dict, output_file: str = "analysis_results.json"):
        """Save analysis results to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {output_file}")


def main():
    """Example usage"""
    
    # Initialize analyzer
    analyzer = VisionAnalyzer()
    
    # Example image path - REPLACE WITH YOUR IMAGE
    image_path = "C:/Users/hriti.DESKTOP-PMBUPVF/Downloads/sales-growth.png"
    
    if not Path(image_path).exists():
        print(f"Please replace 'your_image.jpg' with your actual image path")
        return
    
    print("="*60)
    print("AI VISION IMAGE ANALYZER")
    print("="*60)
    
    # Example 1: Detailed analysis with GPT-4o
    print("\n[1] GPT-4o - Detailed Analysis")
    print("-"*60)
    result = analyzer.analyze_with_gpt4o(image_path, analysis_type="detailed")
    print(result)
    
    # Example 2: Story generation with Claude
    print("\n\n[2] Claude - Story Generation")
    print("-"*60)
    story = analyzer.analyze_with_claude(image_path, analysis_type="story")
    print(story)
    
    # Example 3: Technical analysis with GPT-4o
    print("\n\n[3] GPT-4o - Technical Analysis")
    print("-"*60)
    technical = analyzer.analyze_with_gpt4o(image_path, analysis_type="technical")
    print(technical)
    
    # Example 4: Compare all models
    print("\n\n[4] Comparing All Models")
    print("-"*60)
    comparison = analyzer.compare_models(image_path, analysis_type="story")
    
    # Save comparison results
    analyzer.save_results(comparison, "comparison_results.json")
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)


if __name__ == "__main__":
    main()