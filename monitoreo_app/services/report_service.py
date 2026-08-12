# monitoreo_app/services/report_service.py
import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from django.utils import timezone
from datetime import timedelta
from monitoreo_app.models import NetworkNode, LatencyLog, HTTPEndpoint, HTTPLog, AlertEvent

def generate_nodes_report_pdf(period_days=7):
    """Genera reporte PDF de nodos de red"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    elements.append(Paragraph("Reporte de Monitoreo de Red", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Fecha
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.gray,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(f"Generado: {timezone.now().strftime('%d/%m/%Y %H:%M')}", date_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Estadísticas generales
    nodes = NetworkNode.objects.filter(is_monitored=True)
    total_nodes = nodes.count()
    up_nodes = nodes.filter(status='UP').count()
    down_nodes = nodes.filter(status='DOWN').count()
    warn_nodes = nodes.filter(status='WARN').count()
    
    stats_data = [
        ['Métrica', 'Cantidad'],
        ['Total Nodos', str(total_nodes)],
        ['En línea', str(up_nodes)],
        ['Caídos', str(down_nodes)],
        ['Advertencia', str(warn_nodes)]
    ]
    
    stats_table = Table(stats_data, colWidths=[2*inch, 1*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Lista de nodos
    elements.append(Paragraph("Detalle de Nodos", styles['Heading2']))
    elements.append(Spacer(1, 0.25*inch))
    
    nodes_data = [['Nombre', 'IP', 'Estado', 'Latencia', 'Pérdida']]
    for node in nodes:
        last_log = node.latency_logs.first()
        latency = f"{last_log.latency_ms} ms" if last_log and last_log.latency_ms else 'N/A'
        loss = f"{last_log.packet_loss_pct}%" if last_log else 'N/A'
        status_emoji = '✅' if node.status == 'UP' else '❌' if node.status == 'DOWN' else '⚠️'
        nodes_data.append([
            node.name,
            node.ip_address,
            f"{status_emoji} {node.get_status_display()}",
            latency,
            loss
        ])
    
    nodes_table = Table(nodes_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
    nodes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(nodes_table)
    
    # Servicios HTTP
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Servicios Web", styles['Heading2']))
    elements.append(Spacer(1, 0.25*inch))
    
    http_services = HTTPEndpoint.objects.filter(is_active=True)
    http_data = [['Nombre', 'URL', 'Estado', 'Respuesta']]
    for service in http_services:
        status_emoji = '✅' if service.status == 'UP' else '❌' if service.status == 'DOWN' else '⚠️'
        response = f"{service.last_response_time:.0f} ms" if service.last_response_time else 'N/A'
        http_data.append([
            service.name,
            service.url[:30] + '...' if len(service.url) > 30 else service.url,
            f"{status_emoji} {service.get_status_display()}",
            response
        ])
    
    http_table = Table(http_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 1.5*inch])
    http_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(http_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_excel_report(period_days=7):
    """Genera reporte en Excel"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja 1: Nodos
        nodes = NetworkNode.objects.filter(is_monitored=True)
        nodes_data = []
        for node in nodes:
            last_log = node.latency_logs.first()
            nodes_data.append({
                'Nombre': node.name,
                'IP': node.ip_address,
                'Tipo': node.get_device_type_display(),
                'Estado': node.get_status_display(),
                'Latencia (ms)': last_log.latency_ms if last_log and last_log.latency_ms else None,
                'Pérdida (%)': last_log.packet_loss_pct if last_log else None,
            })
        df_nodes = pd.DataFrame(nodes_data)
        df_nodes.to_excel(writer, sheet_name='Nodos', index=False)
        
        # Hoja 2: Servicios Web
        services = HTTPEndpoint.objects.filter(is_active=True)
        services_data = []
        for service in services:
            services_data.append({
                'Nombre': service.name,
                'URL': service.url,
                'Tipo': service.get_service_type_display() if hasattr(service, 'get_service_type_display') else 'N/A',
                'Estado': service.get_status_display(),
                'Respuesta (ms)': service.last_response_time,
                'SSL Expira': service.ssl_expiry_date.strftime('%d/%m/%Y') if service.ssl_expiry_date else 'N/A'
            })
        df_services = pd.DataFrame(services_data)
        df_services.to_excel(writer, sheet_name='Servicios Web', index=False)
        
        # Hoja 3: Alertas recientes
        alerts = AlertEvent.objects.all().order_by('-created_at')[:50]
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'Fecha': alert.created_at.strftime('%d/%m/%Y %H:%M'),
                'Tipo': alert.event_type,
                'Mensaje': alert.message,
                'Resuelta': '✅' if alert.is_resolved else '❌'
            })
        df_alerts = pd.DataFrame(alerts_data)
        df_alerts.to_excel(writer, sheet_name='Alertas', index=False)
    
    output.seek(0)
    return output