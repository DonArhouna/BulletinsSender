# Configuration des performances pour l'envoi d'emails en masse

class PerformanceConfig:
    """Configuration optimisée pour l'envoi de bulletins en masse"""
    
    # Pool de connexions SMTP
    MAX_SMTP_CONNECTIONS = 50  # Augmenté pour haute performance
    SMTP_CONNECTION_TIMEOUT = 15  # Timeout réduit pour éviter les blocages
    
    # Traitement concurrent
    MAX_CONCURRENT_EMAILS = 25  # Nombre max d'emails traités simultanément
    MAX_WORKERS = 50  # Nombre de threads pour le ThreadPoolExecutor
    
    # Traitement par batch
    DEFAULT_BATCH_SIZE = 100  # Taille des batches pour éviter la surcharge mémoire
    BULLETIN_BATCH_SIZE = 50  # Taille spécifique pour les bulletins PDF
    
    # Délais et retry
    MAX_RETRIES = 3
    RETRY_DELAY_CAP = 5  # Délai maximum entre les tentatives (secondes)
    BATCH_PAUSE = 0.1  # Pause entre les batches (secondes)
    
    # Monitoring
    LOG_BATCH_PROGRESS = True
    LOG_PERFORMANCE_STATS = True
    
    @classmethod
    def get_optimized_settings(cls, email_count: int) -> dict:
        """Retourne des paramètres optimisés selon le nombre d'emails"""
        if email_count < 100:
            return {
                'max_concurrent': 10,
                'batch_size': 25,
                'max_connections': 10
            }
        elif email_count < 1000:
            return {
                'max_concurrent': 20,
                'batch_size': 50,
                'max_connections': 25
            }
        else:
            return {
                'max_concurrent': cls.MAX_CONCURRENT_EMAILS,
                'batch_size': cls.DEFAULT_BATCH_SIZE,
                'max_connections': cls.MAX_SMTP_CONNECTIONS
            }