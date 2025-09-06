"""src/services/analytics_storage.py
Сервис для сохранения результатов аналитики в базу данных.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ReportRequest, ReportStatus, User


class AnalyticsStorageService:
    """Сервис для сохранения результатов аналитики."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_analysis_result(
        self,
        user_id: int,
        full_name: str,
        birth_date: date,
        analysis_result: Dict[str, Any],
        status: ReportStatus = ReportStatus.DONE,
        error_message: Optional[str] = None,
    ) -> ReportRequest:
        """Сохранить результат анализа в базу данных."""
        
        # Формируем текстовый отчёт
        report_text = self._format_analysis_for_storage(analysis_result)
        
        # Создаём запись о запросе отчёта
        report_request = ReportRequest(
            user_id=user_id,
            full_name=full_name,
            birth_date=birth_date,
            status=status,
            result_text=report_text if status == ReportStatus.DONE else None,
            error=error_message if status == ReportStatus.ERROR else None,
        )
        
        self.session.add(report_request)
        return report_request
    
    async def get_user_analyses(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> list[ReportRequest]:
        """Получить последние анализы пользователя."""
        stmt = (
            select(ReportRequest)
            .where(ReportRequest.user_id == user_id)
            .order_by(ReportRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_analysis_by_id(
        self,
        analysis_id: int,
        user_id: int,
    ) -> Optional[ReportRequest]:
        """Получить конкретный анализ по ID."""
        stmt = select(ReportRequest).where(
            ReportRequest.id == analysis_id,
            ReportRequest.user_id == user_id,
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    def _format_analysis_for_storage(self, analysis_result: Dict[str, Any]) -> str:
        """Форматировать результат анализа для хранения в БД."""
        input_data = analysis_result.get("input_data", {})
        calculations = analysis_result.get("calculations", {})
        matrix = analysis_result.get("matrix", {})
        interpretations = analysis_result.get("interpretations", {})
        
        report_lines = []
        
        # Заголовок
        report_lines.append("🔮 **АНАЛИЗ ПО ЦИФРОВОЙ ПСИХОЛОГИИ**")
        report_lines.append("=" * 50)
        
        # Входные данные
        report_lines.append("\n📋 **ВХОДНЫЕ ДАННЫЕ:**")
        report_lines.append(f"• Дата рождения: {input_data.get('birth_date', 'N/A')}")
        
        if input_data.get('has_name', False):
            report_lines.append(f"• Имя: {input_data.get('original_name', 'N/A')}")
            if input_data.get('is_cyrillic', False):
                report_lines.append(f"• Латиницей: {input_data.get('latin_name', 'N/A')}")
        else:
            report_lines.append("• Имя: Не указано")
        
        # Расчёты
        report_lines.append("\n🧮 **РАСЧЁТЫ:**")
        report_lines.append(f"• Число Сознания (ЧС): {calculations.get('consciousness_number', 'N/A')}")
        report_lines.append(f"• Число Действия (ЧД): {calculations.get('action_number', 'N/A')}")
        
        if calculations.get('name_number') is not None:
            report_lines.append(f"• Число Имени: {calculations['name_number']}")
        else:
            report_lines.append("• Число Имени: Не рассчитано")
        
        # Матрица
        if matrix:
            report_lines.append("\n🔢 **МАТРИЦА:**")
            
            # Подсчёт цифр
            digit_counts = matrix.get('digit_counts', {})
            if digit_counts:
                report_lines.append("• Подсчёт цифр:")
                for digit in sorted(digit_counts.keys()):
                    count = digit_counts[digit]
                    report_lines.append(f"  - Цифра {digit}: {count} раз")
            
            # Анализ
            analysis = matrix.get('analysis', {})
            if analysis:
                report_lines.append("• Анализ энергий:")
                if isinstance(analysis, dict):
                    for energy_type, description in analysis.items():
                        report_lines.append(f"  - {energy_type}: {description}")
                else:
                    # Если analysis - это строка
                    report_lines.append(f"  - {analysis}")
        
        # Интерпретации
        if interpretations:
            report_lines.append("\n💭 **ИНТЕРПРЕТАЦИИ:**")
            
            if 'consciousness_interpretation' in interpretations:
                report_lines.append(f"• ЧС: {interpretations['consciousness_interpretation']}")
            
            if 'action_interpretation' in interpretations:
                report_lines.append(f"• ЧД: {interpretations['action_interpretation']}")
            
            if 'name_interpretation' in interpretations:
                report_lines.append(f"• Число Имени: {interpretations['name_interpretation']}")
        
        # Исключения
        exceptions = analysis_result.get("exceptions", {})
        if exceptions.get("has_chs_chd_conflict", False):
            report_lines.append("\n⚠️ **ОСОБЫЕ СЛУЧАИ:**")
            report_lines.append("• Обнаружен конфликт ЧС/ЧД")
        
        return "\n".join(report_lines)
