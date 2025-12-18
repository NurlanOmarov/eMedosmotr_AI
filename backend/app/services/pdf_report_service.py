"""
Сервис для генерации PDF отчетов анализа ИИ
Красиво оформленные отчеты с использованием ReportLab
"""

from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import os

# Многоуровневая регистрация шрифтов с поддержкой кириллицы
# Приоритет: системные TrueType шрифты -> встроенный Unicode CID -> базовый
DEFAULT_FONT = 'Helvetica'
font_registered = False

# Уровень 1: Попытка загрузить системные TrueType шрифты (лучшее качество)
font_paths = [
    # macOS - приоритетный вариант (поддержка 136,000+ символов)
    "/System/Library/Fonts/Arial Unicode.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    # Linux - DejaVu Sans (отличная поддержка кириллицы)
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    # Windows
    "C:\\Windows\\Fonts\\arial.ttf",
    "C:\\Windows\\Fonts\\calibri.ttf",
]

try:
    from reportlab.pdfbase.pdfmetrics import registerFont
    from reportlab.pdfbase.ttfonts import TTFont

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                registerFont(TTFont('CyrillicFont', font_path))
                DEFAULT_FONT = 'CyrillicFont'
                font_registered = True
                print(f"✅ Шрифт успешно зарегистрирован: {font_path}")
                break
            except Exception as e:
                print(f"⚠️ Ошибка регистрации {font_path}: {e}")
                continue

    # Уровень 2: Fallback на встроенный Unicode CID шрифт
    if not font_registered:
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        registerFont(UnicodeCIDFont('HeiseiMin-W3'))
        DEFAULT_FONT = 'HeiseiMin-W3'
        font_registered = True
        print("✅ Использован fallback шрифт HeiseiMin-W3 (встроенный Unicode)")

except Exception as e:
    print(f"⚠️ Критическая ошибка регистрации шрифтов: {e}")
    print("⚠️ Используется базовый Helvetica (ограниченная поддержка кириллицы)")
    DEFAULT_FONT = 'Helvetica'


class PDFReportService:
    """Сервис для генерации PDF отчетов"""

    # Цвета для дизайна (соответствуют UI)
    COLOR_PRIMARY = colors.HexColor('#00d4ff')
    COLOR_WARNING = colors.HexColor('#ffaa00')
    COLOR_DANGER = colors.HexColor('#ff4444')
    COLOR_SUCCESS = colors.HexColor('#00ff88')
    COLOR_BG_DARK = colors.HexColor('#0a0e1a')
    COLOR_BG_CARD = colors.HexColor('#1a1f35')
    COLOR_TEXT = colors.HexColor('#e8edf4')
    COLOR_TEXT_SECONDARY = colors.HexColor('#8892a6')

    def __init__(self):
        """Инициализация сервиса"""
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Настройка стилей для документа"""

        # Используем зарегистрированный шрифт с поддержкой кириллицы
        font_regular = DEFAULT_FONT
        font_bold = DEFAULT_FONT
        font_italic = DEFAULT_FONT

        # Заголовок документа
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.COLOR_PRIMARY,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName=font_bold
        ))

        # Подзаголовок
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=self.COLOR_TEXT_SECONDARY,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName=font_regular
        ))

        # Заголовок секции
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.COLOR_PRIMARY,
            spaceAfter=10,
            spaceBefore=15,
            fontName=font_bold
        ))

        # Обычный текст
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName=font_regular
        ))

        # Текст для disclaimer
        self.styles.add(ParagraphStyle(
            name='Disclaimer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=self.COLOR_WARNING,
            spaceAfter=10,
            alignment=TA_LEFT,
            fontName=font_italic,
            leftIndent=10,
            rightIndent=10
        ))

    def generate_analysis_report(
        self,
        conscript_data: Dict,
        analysis_data: Dict,
        conscript_info: Optional[Dict] = None
    ) -> BytesIO:
        """
        Генерация PDF отчета анализа ИИ

        Args:
            conscript_data: Данные о призывнике
            analysis_data: Результаты анализа ИИ
            conscript_info: Дополнительная информация о призывнике

        Returns:
            BytesIO: PDF файл в памяти
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        # Элементы документа
        story = []

        # Заголовок
        story.append(Paragraph("ОТЧЕТ АНАЛИЗА ИИ", self.styles['CustomTitle']))
        story.append(Paragraph(
            "Автоматический анализ медицинских заключений",
            self.styles['CustomSubtitle']
        ))
        story.append(Spacer(1, 10*mm))

        # Disclaimer
        story.append(self._create_disclaimer())
        story.append(Spacer(1, 5*mm))

        # Информация о призывнике
        if conscript_info:
            story.extend(self._create_conscript_info_section(conscript_info))
            story.append(Spacer(1, 5*mm))

        # Общая статистика
        story.extend(self._create_summary_section(analysis_data))
        story.append(Spacer(1, 5*mm))

        # Уровень риска
        story.extend(self._create_risk_level_section(analysis_data))
        story.append(Spacer(1, 5*mm))

        # Результаты анализа по специалистам
        if analysis_data.get('aiAnalyses'):
            story.extend(self._create_analyses_section(analysis_data['aiAnalyses']))

        # Футер с датой генерации
        story.append(Spacer(1, 10*mm))
        story.append(self._create_footer())

        # Генерация PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _create_disclaimer(self):
        """Создание блока с предупреждением"""
        disclaimer_text = (
            "<b>⚠ ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ:</b><br/>"
            "Данный анализ выполнен с использованием искусственного интеллекта "
            "и носит <b>рекомендательный характер</b>. Результаты ИИ могут содержать "
            "неточности и <b>требуют обязательной проверки</b> квалифицированным "
            "медицинским специалистом. Окончательное решение о категории годности "
            "принимает председатель военно-врачебной комиссии."
        )

        # Таблица для disclaimer с фоном
        disclaimer_table = Table(
            [[Paragraph(disclaimer_text, self.styles['Disclaimer'])]],
            colWidths=[doc_width := 170*mm]
        )
        disclaimer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff4e6')),
            ('BOX', (0, 0), (-1, -1), 1, self.COLOR_WARNING),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))

        return disclaimer_table

    def _create_conscript_info_section(self, conscript_info: Dict):
        """Создание секции с информацией о призывнике"""
        elements = []
        elements.append(Paragraph("ИНФОРМАЦИЯ О ПРИЗЫВНИКЕ", self.styles['SectionHeader']))

        data = [
            ['ФИО:', conscript_info.get('fullName', 'Н/Д')],
            ['ИИН:', conscript_info.get('iin', 'Н/Д')],
            ['Дата рождения:', conscript_info.get('birthDate', 'Н/Д')],
            ['Номер призыва:', conscript_info.get('draftNumber', 'Н/Д')],
        ]

        if conscript_info.get('medicalCommissionDate'):
            data.append(['Дата комиссии:', conscript_info['medicalCommissionDate']])

        table = Table(data, colWidths=[50*mm, 120*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        return elements

    def _create_summary_section(self, analysis_data: Dict):
        """Создание секции с общей статистикой"""
        elements = []
        elements.append(Paragraph("ОБЩАЯ СТАТИСТИКА", self.styles['SectionHeader']))

        total_examinations = len(analysis_data.get('examinations', []))
        ai_analyses = analysis_data.get('aiAnalyses', [])
        mismatches = len([a for a in ai_analyses if a.get('status') in ['MISMATCH', 'PARTIAL_MISMATCH']])

        # Средняя уверенность
        avg_confidence = 0
        if ai_analyses:
            avg_confidence = sum(a.get('confidence', 0) for a in ai_analyses) / len(ai_analyses)

        data = [
            ['Показатель', 'Значение'],
            ['Всего заключений специалистов', str(total_examinations)],
            ['Проанализировано ИИ', str(len(ai_analyses))],
            ['Выявлено несоответствий', str(mismatches)],
            ['Средняя уверенность ИИ', f"{avg_confidence * 100:.1f}%"],
        ]

        table = Table(data, colWidths=[100*mm, 70*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9f9f9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        return elements

    def _create_risk_level_section(self, analysis_data: Dict):
        """Создание секции с уровнем риска"""
        elements = []
        elements.append(Paragraph("ОБЩИЙ УРОВЕНЬ РИСКА", self.styles['SectionHeader']))

        risk_level = analysis_data.get('overallRiskLevel', 'LOW')
        risk_labels = {
            'LOW': 'НИЗКИЙ РИСК',
            'MEDIUM': 'СРЕДНИЙ РИСК',
            'HIGH': 'ВЫСОКИЙ РИСК'
        }
        risk_colors = {
            'LOW': self.COLOR_SUCCESS,
            'MEDIUM': self.COLOR_WARNING,
            'HIGH': self.COLOR_DANGER
        }
        risk_descriptions = {
            'LOW': 'Заключения специалистов соответствуют рекомендациям ИИ. Выявленных проблем нет.',
            'MEDIUM': 'Обнаружены незначительные расхождения. Рекомендуется проверка специалистом.',
            'HIGH': 'Выявлены серьезные несоответствия. Требуется обязательная проверка председателем ВВК.'
        }

        risk_text = f"<b>{risk_labels.get(risk_level, 'НЕИЗВЕСТНО')}</b>"
        risk_para = Paragraph(risk_text, self.styles['CustomBody'])

        desc_para = Paragraph(
            risk_descriptions.get(risk_level, 'Описание недоступно'),
            self.styles['CustomBody']
        )

        risk_table = Table(
            [['Уровень:', risk_para], ['Описание:', desc_para]],
            colWidths=[30*mm, 140*mm]
        )
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f8ff')),
            ('BOX', (0, 0), (-1, -1), 2, risk_colors.get(risk_level, colors.grey)),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        elements.append(risk_table)
        return elements

    def _create_analyses_section(self, ai_analyses: List[Dict]):
        """Создание секции с детальными результатами анализа"""
        elements = []
        elements.append(Paragraph("РЕЗУЛЬТАТЫ АНАЛИЗА ПО СПЕЦИАЛИСТАМ", self.styles['SectionHeader']))

        status_labels = {
            'MATCH': '✓ Соответствует',
            'MISMATCH': '✗ Несоответствие',
            'PARTIAL_MISMATCH': '⚠ Возможно несоответствие',
            'REVIEW_REQUIRED': '⚠ Требуется проверка'
        }

        status_colors = {
            'MATCH': colors.HexColor('#d4edda'),
            'MISMATCH': colors.HexColor('#f8d7da'),
            'PARTIAL_MISMATCH': colors.HexColor('#fff3cd'),
            'REVIEW_REQUIRED': colors.HexColor('#fff3cd')
        }

        for idx, analysis in enumerate(ai_analyses, 1):
            # Заголовок анализа
            specialty_text = f"<b>{idx}. {analysis.get('specialty', 'Н/Д')}</b> (п. {analysis.get('point', 'Н/Д')} пп. {analysis.get('subpoint', 'Н/Д')})"
            elements.append(Paragraph(specialty_text, self.styles['CustomBody']))
            elements.append(Spacer(1, 2*mm))

            # Таблица с деталями
            status = analysis.get('status', 'REVIEW_REQUIRED')
            confidence = analysis.get('confidence', 0)

            data = [
                ['Категория врача:', analysis.get('doctorCategory', 'Н/Д')],
                ['Рекомендация ИИ:', analysis.get('aiRecommendedCategory', 'Н/Д')],
                ['Статус:', status_labels.get(status, status)],
                ['Уверенность:', f"{confidence * 100:.1f}%"],
            ]

            table = Table(data, colWidths=[45*mm, 125*mm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), status_colors.get(status, colors.white)),
                ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))

            elements.append(table)

            # Обоснование
            if analysis.get('reasoning'):
                elements.append(Spacer(1, 2*mm))
                reasoning_text = f"<b>Обоснование:</b> {analysis.get('reasoning')}"
                elements.append(Paragraph(reasoning_text, self.styles['CustomBody']))

            elements.append(Spacer(1, 5*mm))

        return elements

    def _create_footer(self):
        """Создание футера документа"""
        footer_text = (
            f"<i>Отчет сгенерирован автоматически системой eMedosmotr AI<br/>"
            f"Дата и время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>"
        )
        footer_style = ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=self.COLOR_TEXT_SECONDARY,
            alignment=TA_CENTER,
            fontName=DEFAULT_FONT
        )
        return Paragraph(footer_text, footer_style)


# Singleton instance
pdf_report_service = PDFReportService()
