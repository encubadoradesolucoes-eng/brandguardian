"""
Script para popular a tabela de planos de assinatura
"""
from app import app, db, SubscriptionPlan
import json

def seed_subscription_plans():
    """Cria os planos de assinatura padrão"""
    
    plans_data = [
        {
            'name': 'free',
            'display_name': 'Plano Gratuito',
            'price_monthly': 0,
            'max_brands': 5,
            'features': json.dumps({
                'brands': 5,
                'email_notifications': True,
                'whatsapp_notifications': False,
                'rpi_monitoring': False,
                'conflict_alerts': False,
                'pdf_reports': False,
                'api_access': False,
                'priority_support': False
            })
        },
        {
            'name': 'starter',
            'display_name': 'Starter',
            'price_monthly': 2500,
            'max_brands': 10,
            'features': json.dumps({
                'brands': 10,
                'email_notifications': True,
                'whatsapp_notifications': True,
                'rpi_monitoring': True,
                'conflict_alerts': True,
                'pdf_reports': False,
                'api_access': False,
                'priority_support': False
            })
        },
        {
            'name': 'professional',
            'display_name': 'Professional',
            'price_monthly': 8000,
            'max_brands': 25,
            'features': json.dumps({
                'brands': 25,
                'email_notifications': True,
                'whatsapp_notifications': True,
                'rpi_monitoring': True,
                'conflict_alerts': True,
                'pdf_reports': True,
                'api_access': False,
                'priority_support': True
            })
        },
        {
            'name': 'business',
            'display_name': 'Business',
            'price_monthly': 18000,
            'max_brands': 100,
            'features': json.dumps({
                'brands': 100,
                'email_notifications': True,
                'whatsapp_notifications': True,
                'rpi_monitoring': True,
                'conflict_alerts': True,
                'pdf_reports': True,
                'api_access': True,
                'priority_support': True
            })
        },
        {
            'name': 'enterprise',
            'display_name': 'Enterprise',
            'price_monthly': 0,  # Sob consulta
            'max_brands': 9999,
            'features': json.dumps({
                'brands': 'unlimited',
                'email_notifications': True,
                'whatsapp_notifications': True,
                'rpi_monitoring': True,
                'conflict_alerts': True,
                'pdf_reports': True,
                'api_access': True,
                'priority_support': True,
                'custom_integrations': True,
                'dedicated_account_manager': True,
                'sla_guarantee': True
            })
        }
    ]
    
    with app.app_context():
        print("🎯 Populando planos de assinatura...")
        
        for plan_data in plans_data:
            # Verificar se já existe
            existing = SubscriptionPlan.query.filter_by(name=plan_data['name']).first()
            
            if existing:
                print(f"   ⏭️  Plano '{plan_data['display_name']}' já existe")
            else:
                plan = SubscriptionPlan(**plan_data)
                db.session.add(plan)
                print(f"   ✅ Plano '{plan_data['display_name']}' criado")
        
        db.session.commit()
        print("✅ Planos de assinatura configurados com sucesso!")
        
        # Mostrar resumo
        print("\n📊 Planos Disponíveis:")
        all_plans = SubscriptionPlan.query.all()
        for plan in all_plans:
            price_display = f"{plan.price_monthly:,.0f} MT/mês" if plan.price_monthly > 0 else "Gratuito" if plan.name == 'free' else "Sob consulta"
            print(f"   • {plan.display_name}: {price_display} - Até {plan.max_brands} marcas")

if __name__ == '__main__':
    seed_subscription_plans()
