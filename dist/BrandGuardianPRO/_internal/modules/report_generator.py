"""
Módulo de Geração de Relatórios PDF
Cria relatórios profissionais para clientes
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

class BrandReportGenerator:
    def __init__(self, output_path='uploads/reports'):
        self.output_path = output_path
        os.makedirs(output_path, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Define estilos personalizados"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#8b5cf6'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e1b4b'),
            spaceBefore=20,
            spaceAfter=12,
            borderPadding=5,
            backColor=colors.HexColor('#f3f4f6')
        ))
    
    def generate_brand_portfolio_report(self, user, brands):
        """Gera relatório completo da carteira de marcas"""
        filename = f"portfolio_{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_path, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        
        story = []
        
        # Header
        story.append(Paragraph("M24 BRAND GUARDIAN PRO", self.styles['CustomTitle']))
        story.append(Paragraph("Relatório de Carteira de Marcas", self.styles['Heading2']))
        story.append(Spacer(1, 0.5*cm))
        
        # Info do Cliente
        client_data = [
            ['Cliente:', user.name or user.username],
            ['Email:', user.email],
            ['Plano:', user.subscription_plan.upper()],
            ['Data do Relatório:', datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]
        client_table = Table(client_data, colWidths=[4*cm, 12*cm])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(client_table)
        story.append(Spacer(1, 1*cm))
        
        # Resumo Executivo
        story.append(Paragraph("RESUMO EXECUTIVO", self.styles['SectionHeader']))
        summary_data = [
            ['Total de Marcas:', str(len(brands))],
            ['Marcas Aprovadas:', str(sum(1 for b in brands if b.status == 'approved'))],
            ['Em Análise:', str(sum(1 for b in brands if b.status in ['under_study', 'waiting_admin']))],
            ['Alto Risco:', str(sum(1 for b in brands if b.risk_level == 'high'))],
        ]
        summary_table = Table(summary_data, colWidths=[8*cm, 8*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef3c7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fbbf24'))
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 1*cm))
        
        # Detalhes das Marcas
        story.append(Paragraph("DETALHAMENTO DAS MARCAS", self.styles['SectionHeader']))
        
        for brand in brands:
            brand_data = [
                ['Marca:', brand.name],
                ['Processo:', brand.process_number or 'Em registro'],
                ['Status:', brand.status.replace('_', ' ').title()],
                ['Classes Nice:', brand.nice_classes or 'N/A'],
                ['Nível de Risco:', brand.risk_level.upper() if brand.risk_level else 'N/A'],
                ['Data de Submissão:', brand.submission_date.strftime('%d/%m/%Y') if brand.submission_date else 'N/A']
            ]
            
            brand_table = Table(brand_data, colWidths=[4*cm, 12*cm])
            brand_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(brand_table)
            story.append(Spacer(1, 0.5*cm))
        
        # Footer
        story.append(Spacer(1, 2*cm))
        story.append(Paragraph(
            "Este relatório foi gerado automaticamente pelo M24 Brand Guardian PRO",
            self.styles['Normal']
        ))
        story.append(Paragraph(
            f"© {datetime.now().year} M24 - Todos os direitos reservados",
            self.styles['Normal']
        ))
        
        # Build PDF
        doc.build(story)
        return filepath
    
    def generate_conflict_alert_report(self, brand, conflicts):
        """Gera relatório de alerta de conflitos para uma marca específica"""
        filename = f"conflicts_{brand.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_path, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        
        story = []
        
        # Header
        story.append(Paragraph("⚠️ ALERTA DE CONFLITO DE MARCA", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*cm))
        
        # Info da Marca
        story.append(Paragraph("MARCA PROTEGIDA", self.styles['SectionHeader']))
        brand_info = [
            ['Nome:', brand.name],
            ['Processo INPI:', brand.process_number or 'Em registro'],
            ['Classes:', brand.nice_classes or 'N/A'],
            ['Data:', datetime.now().strftime('%d/%m/%Y')]
        ]
        brand_table = Table(brand_info, colWidths=[4*cm, 12*cm])
        brand_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef3c7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fbbf24'))
        ]))
        story.append(brand_table)
        story.append(Spacer(1, 1*cm))
        
        # Conflitos Detectados
        story.append(Paragraph(f"CONFLITOS DETECTADOS ({len(conflicts)})", self.styles['SectionHeader']))
        
        for idx, conflict in enumerate(conflicts, 1):
            conflict_data = [
                [f"Conflito #{idx}"],
                ['Marca Conflitante:', conflict.conflicting_mark_name],
                ['Processo:', conflict.conflicting_mark_number],
                ['Similaridade:', f"{conflict.similarity_score}%"],
                ['Tipo:', conflict.conflict_type.title()],
                ['Status:', conflict.status.title()]
            ]
            
            # Cor baseada na similaridade
            if conflict.similarity_score > 80:
                bg_color = colors.HexColor('#fee2e2')  # Vermelho claro
            elif conflict.similarity_score > 60:
                bg_color = colors.HexColor('#fed7aa')  # Laranja claro
            else:
                bg_color = colors.HexColor('#dbeafe')  # Azul claro
            
            conflict_table = Table(conflict_data, colWidths=[4*cm, 12*cm])
            conflict_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), bg_color),
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('SPAN', (0, 0), (-1, 0))
            ]))
            story.append(conflict_table)
            story.append(Spacer(1, 0.5*cm))
        
        # Recomendações
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("RECOMENDAÇÕES", self.styles['SectionHeader']))
        recommendations = """
        <b>1. Análise Jurídica:</b> Consulte um advogado especializado em Propriedade Intelectual.<br/>
        <b>2. Oposição:</b> Considere apresentar oposição aos pedidos conflitantes dentro do prazo legal.<br/>
        <b>3. Monitoramento:</b> Continue acompanhando o andamento dos processos através do M24 PRO.<br/>
        <b>4. Documentação:</b> Reúna evidências de uso anterior da marca, se aplicável.
        """
        story.append(Paragraph(recommendations, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return filepath


def generate_weekly_report(user_id):
    """Gera relatório semanal para um usuário"""
    from app import User, Brand, BrandConflict, db
    
    user = User.query.get(user_id)
    if not user:
        return None
    
    brands = Brand.query.filter_by(user_id=user_id).all()
    generator = BrandReportGenerator()
    
    return generator.generate_brand_portfolio_report(user, brands)
