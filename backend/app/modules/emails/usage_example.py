"""
Exemple d'utilisation du service email optimisé pour l'envoi en masse
"""

from app.modules.emails.service import email_service
from app.modules.emails import schemas
import asyncio

async def example_bulk_bulletins():
    """Exemple d'envoi de bulletins en masse avec monitoring"""
    
    # Simulation de fichiers PDF (remplacez par vos vrais fichiers)
    class MockFile:
        def __init__(self, filename, content=b"mock pdf content"):
            self.filename = filename
            self.file = MockFileObject(content)
    
    class MockFileObject:
        def __init__(self, content):
            self.content = content
            self.position = 0
        
        def read(self):
            return self.content
        
        def seek(self, pos):
            self.position = pos
    
    # Créer une requête avec plusieurs fichiers
    files = [MockFile(f"bulletin_{i}.pdf") for i in range(100)]  # 100 bulletins
    
    request = schemas.SendBulletinsRequest(
        files=files,
        subject="Votre bulletin de paie",
        message="Veuillez trouver ci-joint votre bulletin de paie.",
        sender_email="rh@entreprise.com"
    )
    
    print("🚀 Démarrage de l'envoi de 100 bulletins...")
    
    # Envoi avec configuration optimisée automatique
    response = await email_service.send_bulletins_concurrent(
        request, 
        max_concurrent=25  # Ajusté automatiquement selon le volume
    )
    
    # Affichage des résultats
    print(f"\n📊 RÉSULTATS:")
    print(f"Total fichiers: {response.total_files}")
    print(f"Traités: {response.processed_files}")
    print(f"Succès: {response.successful_sends}")
    print(f"Échecs: {response.failed_sends}")
    
    # Statistiques de performance
    stats = email_service.get_performance_stats()
    print(f"\n⚡ PERFORMANCE:")
    print(f"Débit: {stats['emails_per_second']:.1f} emails/s")
    print(f"Taux de succès: {stats['success_rate']:.1f}%")
    print(f"Temps moyen par batch: {stats['average_batch_time']:.2f}s")
    
    # Recommandations d'optimisation
    print(f"\n💡 RECOMMANDATIONS:")
    for rec in stats['recommendations']:
        print(f"  {rec}")

def example_bulk_emails():
    """Exemple d'envoi d'emails simples en masse"""
    
    # Créer une liste d'emails (remplacez par vos vraies données)
    from app.modules.emails.models import Email
    
    emails = []
    for i in range(500):  # 500 emails
        email = Email(
            recipient_email=f"user{i}@example.com",
            subject="Newsletter mensuelle",
            body=f"<h1>Bonjour utilisateur {i}</h1><p>Voici votre newsletter.</p>",
            sender_email="newsletter@entreprise.com"
        )
        emails.append(email)
    
    print("📧 Démarrage de l'envoi de 500 emails...")
    
    # Envoi optimisé avec configuration automatique
    results = email_service.send_bulk_emails_optimized(emails)
    
    # Statistiques
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 RÉSULTATS:")
    print(f"Total: {total_count}")
    print(f"Succès: {success_count}")
    print(f"Échecs: {total_count - success_count}")
    print(f"Taux de succès: {(success_count/total_count*100):.1f}%")
    
    # Performance détaillée
    stats = email_service.get_performance_stats()
    print(f"\n⚡ PERFORMANCE:")
    print(f"Débit: {stats['emails_per_second']:.1f} emails/s")
    print(f"Batches traités: {stats['batches_completed']}")

def example_configuration_adaptive():
    """Exemple de configuration adaptative selon le volume"""
    
    volumes = [50, 200, 1000, 5000]
    
    print("🔧 CONFIGURATION ADAPTATIVE:")
    print("=" * 50)
    
    for volume in volumes:
        config = email_service.get_optimized_config(volume)
        print(f"\n📊 Volume: {volume} emails")
        print(f"  Max concurrent: {config['max_concurrent']}")
        print(f"  Taille batch: {config['batch_size']}")
        print(f"  Connexions SMTP: {config['max_connections']}")

if __name__ == "__main__":
    print("🎯 EXEMPLES D'UTILISATION DU SERVICE EMAIL OPTIMISÉ")
    print("=" * 60)
    
    # 1. Configuration adaptative
    example_configuration_adaptive()
    
    # 2. Envoi d'emails simples (décommentez pour tester)
    # example_bulk_emails()
    
    # 3. Envoi de bulletins (décommentez pour tester)
    # asyncio.run(example_bulk_bulletins())
    
    print("\n✅ Exemples terminés!")
    print("\n💡 CONSEILS D'OPTIMISATION:")
    print("- Utilisez send_bulk_emails_optimized() pour les emails simples")
    print("- Utilisez send_bulletins_concurrent() pour les bulletins PDF")
    print("- La configuration s'adapte automatiquement au volume")
    print("- Surveillez les logs pour les recommandations d'optimisation")
    print("- Ajustez MAX_SMTP_CONNECTIONS selon votre serveur SMTP")