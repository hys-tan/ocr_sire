import os
import logging
import spacy
import joblib

logger = logging.getLogger("ExtractorSIRE.NLP")
logger.setLevel(logging.INFO)

class NLPService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NLPService, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance
        
    def initialize(self):
        self.classifier = None
        self.ner_model = None
        
        # Cargar modelo Scikit-Learn
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models", "block_classifier.pkl")
        try:
            if os.path.exists(model_path):
                self.classifier = joblib.load(model_path)
                logger.info("Modelo ML Clasificador de Bloques cargado exitosamente.")
            else:
                logger.warning(f"No se encontró el modelo clasificador en {model_path}. Fase de ML deshabilitada.")
        except Exception as e:
            logger.error(f"Error cargando el modelo de bloques: {e}")
            
        # Cargar modelo NER de spaCy
        try:
            logger.info("Cargando modelo spaCy NER (es_core_news_sm)...")
            self.ner_model = spacy.load("es_core_news_sm")
            logger.info("Modelo spaCy cargado exitosamente.")
        except OSError:
            logger.warning("No se encontró 'es_core_news_sm'. Ejecuta: python -m spacy download es_core_news_sm")
            # En producción, intentaríamos descargarlo aquí o fallar limpiamente.

    def clasificar_linea(self, texto: str) -> str:
        """Devuelve la clase predicha para la línea usando Naive Bayes."""
        if not self.classifier or not texto.strip():
            return "OTROS"
        pred = self.classifier.predict([texto])
        return pred[0]
        
    def extraer_entidad_ner(self, texto: str, expected_labels=None) -> str:
        """Extrae entidades nombradas de un texto usando spaCy.
        Para un Emisor o Receptor, buscamos preferentemente ORG o PER.
        """
        if not self.ner_model or not texto.strip():
            return ""
            
        if expected_labels is None:
            expected_labels = ["ORG", "PER"]
            
        doc = self.ner_model(texto)
        entidades_encontradas = []
        
        for ent in doc.ents:
            if ent.label_ in expected_labels:
                entidades_encontradas.append(ent.text)
                
        if entidades_encontradas:
            # Retorna la entidad más larga encontrada que coincida con el tipo
            entidades_encontradas.sort(key=len, reverse=True)
            ent_extraida = entidades_encontradas[0]
            logger.info(f"spaCy detectó Entidad ({expected_labels}): '{ent_extraida}' en el texto '{texto}'")
            return ent_extraida
            
        return ""

# Instancia global singleton
nlp_service = NLPService()
