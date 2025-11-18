import time
import logging
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class BatchStats:
    """Statistiques d'un batch d'envoi"""
    batch_id: int
    size: int
    success_count: int
    failure_count: int
    duration: float
    start_time: datetime
    end_time: datetime

@dataclass
class PerformanceMetrics:
    """Métriques de performance globales"""
    total_emails: int = 0
    successful_sends: int = 0
    failed_sends: int = 0
    total_duration: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = None
    batch_stats: List[BatchStats] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Taux de succès en pourcentage"""
        if self.total_emails == 0:
            return 0.0
        return (self.successful_sends / self.total_emails) * 100
    
    @property
    def emails_per_second(self) -> float:
        """Nombre d'emails par seconde"""
        if self.total_duration == 0:
            return 0.0
        return self.successful_sends / self.total_duration
    
    @property
    def average_batch_time(self) -> float:
        """Temps moyen par batch"""
        if not self.batch_stats:
            return 0.0
        return sum(batch.duration for batch in self.batch_stats) / len(self.batch_stats)

class PerformanceMonitor:
    """Moniteur de performance pour l'envoi d'emails en masse"""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.current_batch_id = 0
        self.batch_start_time = None
    
    def start_session(self, total_emails: int):
        """Démarre une session de monitoring"""
        self.metrics = PerformanceMetrics(
            total_emails=total_emails,
            start_time=datetime.now()
        )
        logger.info(f"🚀 Début session d'envoi: {total_emails} emails")
    
    def start_batch(self, batch_size: int) -> int:
        """Démarre le monitoring d'un batch"""
        self.current_batch_id += 1
        self.batch_start_time = time.time()
        logger.info(f"📦 Batch {self.current_batch_id}: {batch_size} emails")
        return self.current_batch_id
    
    def end_batch(self, batch_id: int, success_count: int, failure_count: int):
        """Termine le monitoring d'un batch"""
        if self.batch_start_time is None:
            return
            
        duration = time.time() - self.batch_start_time
        batch_size = success_count + failure_count
        
        batch_stats = BatchStats(
            batch_id=batch_id,
            size=batch_size,
            success_count=success_count,
            failure_count=failure_count,
            duration=duration,
            start_time=datetime.fromtimestamp(self.batch_start_time),
            end_time=datetime.now()
        )
        
        self.metrics.batch_stats.append(batch_stats)
        self.metrics.successful_sends += success_count
        self.metrics.failed_sends += failure_count
        
        # Calcul du débit pour ce batch
        emails_per_sec = success_count / duration if duration > 0 else 0
        
        logger.info(
            f"✅ Batch {batch_id} terminé: {success_count}/{batch_size} "
            f"({(success_count/batch_size*100):.1f}%) en {duration:.2f}s "
            f"({emails_per_sec:.1f} emails/s)"
        )
        
        self.batch_start_time = None
    
    def end_session(self):
        """Termine la session de monitoring"""
        self.metrics.end_time = datetime.now()
        self.metrics.total_duration = (
            self.metrics.end_time - self.metrics.start_time
        ).total_seconds()
        
        self._log_final_stats()
    
    def _log_final_stats(self):
        """Affiche les statistiques finales"""
        m = self.metrics
        
        logger.info("=" * 60)
        logger.info("📊 STATISTIQUES FINALES D'ENVOI")
        logger.info("=" * 60)
        logger.info(f"📧 Total emails: {m.total_emails}")
        logger.info(f"✅ Envoyés avec succès: {m.successful_sends}")
        logger.info(f"❌ Échecs: {m.failed_sends}")
        logger.info(f"📈 Taux de succès: {m.success_rate:.1f}%")
        logger.info(f"⏱️  Durée totale: {m.total_duration:.2f}s")
        logger.info(f"🚀 Débit moyen: {m.emails_per_second:.1f} emails/s")
        logger.info(f"📦 Nombre de batches: {len(m.batch_stats)}")
        logger.info(f"⏱️  Temps moyen par batch: {m.average_batch_time:.2f}s")
        
        if m.batch_stats:
            fastest_batch = min(m.batch_stats, key=lambda b: b.duration)
            slowest_batch = max(m.batch_stats, key=lambda b: b.duration)
            
            logger.info(f"🏃 Batch le plus rapide: {fastest_batch.duration:.2f}s")
            logger.info(f"🐌 Batch le plus lent: {slowest_batch.duration:.2f}s")
        
        logger.info("=" * 60)
    
    def get_current_stats(self) -> Dict:
        """Retourne les statistiques actuelles"""
        return {
            'total_emails': self.metrics.total_emails,
            'successful_sends': self.metrics.successful_sends,
            'failed_sends': self.metrics.failed_sends,
            'success_rate': self.metrics.success_rate,
            'emails_per_second': self.metrics.emails_per_second,
            'batches_completed': len(self.metrics.batch_stats),
            'average_batch_time': self.metrics.average_batch_time
        }
    
    def get_recommendations(self) -> List[str]:
        """Génère des recommandations d'optimisation"""
        recommendations = []
        m = self.metrics
        
        if m.success_rate < 90:
            recommendations.append(
                "⚠️  Taux de succès faible (<90%). Vérifiez la configuration SMTP et la qualité des adresses email."
            )
        
        if m.emails_per_second < 5:
            recommendations.append(
                "🐌 Débit faible (<5 emails/s). Considérez augmenter le nombre de connexions SMTP ou la concurrence."
            )
        
        if m.average_batch_time > 30:
            recommendations.append(
                "⏰ Temps de batch élevé (>30s). Réduisez la taille des batches ou augmentez la concurrence."
            )
        
        if len(m.batch_stats) > 0:
            batch_variance = max(b.duration for b in m.batch_stats) - min(b.duration for b in m.batch_stats)
            if batch_variance > 10:
                recommendations.append(
                    "📊 Grande variance dans les temps de batch. Vérifiez la stabilité de la connexion réseau."
                )
        
        if not recommendations:
            recommendations.append("🎉 Performance optimale ! Aucune amélioration suggérée.")
        
        return recommendations