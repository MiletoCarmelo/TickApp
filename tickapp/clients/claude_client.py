"""
Client Claude API simple et modulaire

Usage:
    from claude_client import ClaudeClient
    
    client = ClaudeClient(api_key="sk-ant-...")
    client.add_prompt("Décris cette image")
    client.add_image("photo.jpg")
    response = client.call()
    print(response)
"""

import anthropic
import base64
from pathlib import Path
from typing import List, Optional, Dict, Any


class ClaudeClient:
    """
    Client simple pour l'API Claude
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialise le client Claude
        
        Args:
            api_key: Clé API Anthropic
            model: Modèle à utiliser (défaut: claude-sonnet-4-20250514)
        """
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Contenu de la requête (reset à chaque appel)
        self.content: List[Dict[str, Any]] = []
    
    def login(self) -> bool:
        """
        Vérifie que l'API key est valide
        
        Returns:
            True si la connexion est valide
        """
        try:
            # Test simple avec un petit appel
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{
                    "role": "user",
                    "content": "Hi"
                }]
            )
            return True
        except anthropic.APIError as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def add_prompt(self, text: str):
        """
        Ajoute un prompt texte
        
        Args:
            text: Le texte du prompt
        """
        self.content.append({
            "type": "text",
            "text": text
        })
    
    def add_image(self, image_path: str, media_type: Optional[str] = None):
        """
        Ajoute une image
        
        Args:
            image_path: Chemin vers l'image
            media_type: Type MIME (auto-détecté si None)
        """
        img_file = Path(image_path)
        
        if not img_file.exists():
            raise FileNotFoundError(f"Image introuvable: {image_path}")
        
        # Lire et encoder l'image
        with open(img_file, "rb") as f:
            img_data = base64.standard_b64encode(f.read()).decode("utf-8")
        
        # Détecter le type MIME si non fourni
        if media_type is None:
            ext = img_file.suffix.lower()
            media_type = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
                ".gif": "image/gif"
            }.get(ext, "image/jpeg")
        
        self.content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": img_data
            }
        })
    
    def add_images(self, image_paths: List[str]):
        """
        Ajoute plusieurs images
        
        Args:
            image_paths: Liste des chemins vers les images
        """
        for img_path in image_paths:
            self.add_image(img_path)
    
    def call(
        self, 
        max_tokens: int = 4096,
        temperature: float = 1.0,
        reset_after: bool = True
    ) -> str:
        """
        Appelle l'API Claude
        
        Args:
            max_tokens: Nombre maximum de tokens dans la réponse
            temperature: Température (0-1, plus haut = plus créatif)
            reset_after: Reset le contenu après l'appel
            
        Returns:
            La réponse de Claude (texte brut)
        """
        if not self.content:
            raise ValueError("Aucun contenu à envoyer (utilisez add_prompt ou add_image)")
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{
                    "role": "user",
                    "content": self.content
                }]
            )
            
            # Extraire le texte de la réponse
            response_text = response.content[0].text
            
            # Reset si demandé
            if reset_after:
                self.reset()
            
            return response_text
            
        except anthropic.APIError as e:
            print(f"❌ Erreur API: {e}")
            raise
    
    def call_json(
        self, 
        max_tokens: int = 4096,
        temperature: float = 1.0,
        reset_after: bool = True
    ) -> Dict:
        """
        Appelle l'API Claude et parse la réponse en JSON
        
        Args:
            max_tokens: Nombre maximum de tokens dans la réponse
            temperature: Température (0-1)
            reset_after: Reset le contenu après l'appel
            
        Returns:
            La réponse parsée en dictionnaire JSON
        """
        import json
        import re
        
        response_text = self.call(
            max_tokens=max_tokens,
            temperature=temperature,
            reset_after=reset_after
        )
        
        # Extraire le JSON (Claude peut ajouter du texte autour)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group())
        else:
            raise ValueError("Aucun JSON trouvé dans la réponse")
    
    def reset(self):
        """
        Reset le contenu (vide les prompts et images)
        """
        self.content = []
    
    def get_content_summary(self) -> str:
        """
        Retourne un résumé du contenu actuel
        
        Returns:
            Résumé du contenu
        """
        text_count = sum(1 for c in self.content if c["type"] == "text")
        image_count = sum(1 for c in self.content if c["type"] == "image")
        
        return f"Contenu: {text_count} prompt(s), {image_count} image(s)"


# Exemple d'utilisation
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialiser le client
    client = ClaudeClient(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Vérifier la connexion
    print("🔐 Test de connexion...")
    if client.login():
        print("✅ Connexion réussie\n")
    else:
        print("❌ Échec de connexion")
        exit(1)
    
    # Exemple 1: Simple prompt texte
    print("=" * 60)
    print("EXEMPLE 1: Prompt texte simple")
    print("=" * 60)
    
    client.add_prompt("Écris un haiku sur la programmation")
    response = client.call(max_tokens=100)
    print(f"Réponse:\n{response}\n")
    
    # Exemple 2: Analyse d'image (si tu as une image de test)
    print("=" * 60)
    print("EXEMPLE 2: Analyse d'image")
    print("=" * 60)
    
    # Décommenter si tu as une image de test
    # client.add_image("test_image.jpg")
    # client.add_prompt("Décris cette image en détail")
    # response = client.call()
    # print(f"Réponse:\n{response}\n")
    
    # Exemple 3: Plusieurs images + prompt
    print("=" * 60)
    print("EXEMPLE 3: Plusieurs images")
    print("=" * 60)
    
    # Décommenter si tu as plusieurs images
    # client.add_images(["image1.jpg", "image2.jpg"])
    # client.add_prompt("Compare ces deux images")
    # response = client.call()
    # print(f"Réponse:\n{response}\n")
    
    # Exemple 4: Réponse JSON
    print("=" * 60)
    print("EXEMPLE 4: Réponse JSON")
    print("=" * 60)
    
    client.add_prompt("""
Liste 3 langages de programmation populaires en JSON:
{
  "languages": [
    {"name": "...", "year": 1995},
    ...
  ]
}
""")
    
    try:
        json_response = client.call_json(max_tokens=200)
        print(f"Réponse JSON:\n{json_response}\n")
    except Exception as e:
        print(f"Erreur: {e}")
    
    print("✅ Tous les exemples terminés")