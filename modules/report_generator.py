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


    def generate_brand_dossier(self, brand, entity=None):
        """Gera um dossier completo de um único processo/marca"""
        filename = f"dossier_{brand.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_path, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        
        story = []
        
        # Header Pro
        story.append(Paragraph("M24 BRAND GUARDIAN - DOSSIER TÉCNICO", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*cm))
        
        # Logo da Marca (se houver)
        if brand.image_data:
            # Salvar temporariamente para o PDF
            temp_img_path = f"uploads/temp_logo_{brand.id}.png"
            with open(temp_img_path, 'wb') as f:
                f.write(brand.image_data)
            try:
                img = Image(temp_img_path, width=5*cm, height=5*cm)
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 0.5*cm))
            except:
                pass
        
        # IDENTIFICAÇÃO PRINCIPAL
        story.append(Paragraph("1. IDENTIFICAÇÃO DO ATIVO", self.styles['SectionHeader']))
        id_data = [
            ['Nome da Marca:', brand.name],
            ['Processo M24:', brand.process_number or 'N/A'],
            ['Sufixo Jurídico:', brand.suffix or 'N/A'],
            ['Categoria:', brand.category or 'N/A'],
            ['Tipo de PI:', (brand.property_type or 'Marca').upper()],
            ['Status Atual:', brand.status.upper().replace('_', ' ')],
            ['Nacionalidade:', brand.nationality or 'N/A']
        ]
        id_table = Table(id_data, colWidths=[5*cm, 11*cm])
        id_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(id_table)

        # INFORMAÇÃO DO TITULAR
        story.append(Paragraph("2. INFORMAÇÃO DO TITULAR", self.styles['SectionHeader']))
        owner_data = [
            ['Nome/Razão Social:', brand.owner_name or 'N/A'],
            ['NUIT:', brand.owner_nuit or 'N/A'],
            ['Email de Contato:', brand.owner_email or 'N/A'],
            ['Telefone:', brand.owner_phone or 'N/A'],
            ['Endereço Completo:', Paragraph(brand.full_address or 'N/D', self.styles['Normal'])]
        ]
        owner_table = Table(owner_data, colWidths=[5*cm, 11*cm])
        owner_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fef3c7')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(owner_table)
        
        # DADOS TÉCNICOS BPI
        story.append(Paragraph("3. DADOS TÉCNICOS E DATAS LEGAIS", self.styles['SectionHeader']))
        tech_data = [
            ['Classes Nice:', brand.nice_classes or 'N/A'],
            ['Data de Depósito:', brand.filing_date or 'N/D'],
            ['Publicação BPI:', brand.publication_date_bpi or 'N/D'],
            ['Boletim nº:', brand.bulletin_number or 'N/D'],
            ['Prazo Oposição:', brand.opposition_deadline or 'N/D'],
            ['Data Concessão:', brand.grant_date or 'Pendente'],
            ['Validade / Expira:', brand.expiry_date or 'N/D'],
            ['Próxima Renovação:', brand.next_renewal_date or 'N/D'],
            ['Taxa Tripla:', 'SIM (Em Mora)' if brand.triple_fee == 'sim' else 'NÃO']
        ]
        tech_table = Table(tech_data, colWidths=[5*cm, 11*cm])
        tech_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(tech_table)

        # HISTÓRICO E DECISÕES
        story.append(Paragraph("4. HISTÓRICO E DECISÕES JURÍDICAS", self.styles['SectionHeader']))
        decision_data = [
            ['Prazo de Recurso:', brand.appeal_deadline or 'N/A'],
            ['Motivo da Recusa:', Paragraph(brand.refusal_reason or 'Nenhum registro', self.styles['Normal'])],
            ['Data de Renúncia:', brand.renunciation_date or 'N/A'],
            ['Recusa Definitiva:', brand.final_refusal_date or 'N/A'],
            ['Caducidade Definitiva:', brand.definite_expiry_date or 'N/A'],
            ['Próxima Ação:', brand.next_action or 'N/A']
        ]
        decision_table = Table(decision_data, colWidths=[5*cm, 11*cm])
        decision_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fee2e2')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(decision_table)

        # OBSERVAÇÕES E NOTAS
        story.append(Paragraph("5. OBSERVAÇÕES TÉCNICAS", self.styles['SectionHeader']))
        obs_text = brand.observations or "Nenhuma observação técnica registrada para este processo."
        story.append(Paragraph(obs_text, self.styles['Normal']))
        
        if brand.admin_notes:
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph("NOTAS ADMINISTRATIVAS:", self.styles['Helvetica-Bold'] if 'Helvetica-Bold' in self.styles else self.styles['Normal']))
            story.append(Paragraph(brand.admin_notes, self.styles['Normal']))

        # TITULARIDADE
        if entity:
            story.append(Paragraph("6. TITULARIDADE E ENDEREÇO", self.styles['SectionHeader']))
            ent_data = [
                ['Nome / Razão:', entity.name],
                ['NUIT:', entity.nuit or 'N/A'],
                ['Email:', entity.email],
                ['Telefone:', entity.phone or 'N/A'],
                ['Endereço:', f"{entity.address}, {entity.city}"]
            ]
            ent_table = Table(ent_data, colWidths=[5*cm, 11*cm])
            ent_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#dcfce7')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(ent_table)

        # DIAGNÓSTICO IA
        story.append(Paragraph("7. DIAGNÓSTICO DE PROTEÇÃO M24", self.styles['SectionHeader']))
        risk_color = colors.green if brand.risk_level == 'low' else (colors.orange if brand.risk_level == 'medium' else colors.red)
        diag_data = [
            ['Nível de Risco:', brand.risk_level.upper()],
            ['Score Global:', f"{brand.risk_score or 0}%"],
            ['Fonético:', f"{brand.phonetic_score or 0}%"],
            ['Visual:', f"{brand.visual_score or 0}%"],
            ['Conflitos Det.:', str(len(brand.conflicts) if hasattr(brand, 'conflicts') else 0)]
        ]
        diag_table = Table(diag_data, colWidths=[5*cm, 11*cm])
        diag_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fef3c7')),
            ('TEXTCOLOR', (1, 0), (1, 0), risk_color),
            ('FONTNAME', (1, 0), (1, 1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(diag_table)

        if brand.observations:
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph("OBSERVAÇÕES ADICIONAIS:", self.styles['Heading3']))
            story.append(Paragraph(brand.observations, self.styles['Normal']))

        # Footer
        story.append(Spacer(1, 2*cm))
        footer = f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | Documento de Uso Exclusivo e Confidencial."
        story.append(Paragraph(footer, self.styles['Normal']))
        
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
