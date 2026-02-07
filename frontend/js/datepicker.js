/**
 * Datepicker Moderno - Componente de calendario personalizado
 * Compatible con modo oscuro y temas de color
 */

class Datepicker {
    constructor(inputElement, options = {}) {
        this.input = typeof inputElement === 'string'
            ? document.querySelector(inputElement)
            : inputElement;

        if (!this.input) {
            console.error('Datepicker: No se encontró el elemento input');
            return;
        }

        // Opciones por defecto
        this.options = {
            format: 'YYYY-MM-DD',
            locale: localStorage.getItem('language') || 'es',
            minDate: null,
            maxDate: null,
            onChange: null,
            ...options
        };

        // Estado
        this.selectedDate = this.input.value ? new Date(this.input.value + 'T00:00:00') : null;
        this.viewDate = this.selectedDate ? new Date(this.selectedDate) : new Date();
        this.isOpen = false;

        // Traducciones
        this.translations = {
            es: {
                months: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
                monthsShort: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                              'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
                weekdays: ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'],
                weekdaysMin: ['D', 'L', 'M', 'X', 'J', 'V', 'S'],
                today: 'Hoy',
                clear: 'Limpiar',
                close: 'Cerrar',
                selectDate: 'Seleccionar fecha'
            },
            en: {
                months: ['January', 'February', 'March', 'April', 'May', 'June',
                         'July', 'August', 'September', 'October', 'November', 'December'],
                monthsShort: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                weekdays: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                weekdaysMin: ['S', 'M', 'T', 'W', 'T', 'F', 'S'],
                today: 'Today',
                clear: 'Clear',
                close: 'Close',
                selectDate: 'Select date'
            },
            fr: {
                months: ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                         'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'],
                monthsShort: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
                              'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'],
                weekdays: ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'],
                weekdaysMin: ['D', 'L', 'M', 'M', 'J', 'V', 'S'],
                today: "Aujourd'hui",
                clear: 'Effacer',
                close: 'Fermer',
                selectDate: 'Sélectionner une date'
            }
        };

        this.init();
    }

    get t() {
        return this.translations[this.options.locale] || this.translations.es;
    }

    init() {
        // Ocultar input original de tipo date
        this.input.type = 'hidden';

        // Crear wrapper
        this.wrapper = document.createElement('div');
        this.wrapper.className = 'datepicker-wrapper';
        this.input.parentNode.insertBefore(this.wrapper, this.input);
        this.wrapper.appendChild(this.input);

        // Crear input visual
        this.displayInput = document.createElement('div');
        this.displayInput.className = 'datepicker-input';
        this.displayInput.innerHTML = `
            <span class="datepicker-input-text">${this.formatDisplayDate(this.selectedDate)}</span>
            <span class="datepicker-input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
            </span>
        `;
        this.wrapper.appendChild(this.displayInput);

        // Crear calendario
        this.calendar = document.createElement('div');
        this.calendar.className = 'datepicker-calendar';
        this.wrapper.appendChild(this.calendar);

        // Event listeners
        this.displayInput.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });

        document.addEventListener('click', (e) => {
            if (!this.wrapper.contains(e.target)) {
                this.close();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });

        // Renderizar calendario
        this.render();
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        // Cerrar otros datepickers abiertos
        document.querySelectorAll('.datepicker-calendar.open').forEach(cal => {
            cal.classList.remove('open');
        });

        this.isOpen = true;
        this.calendar.classList.add('open');
        this.displayInput.classList.add('active');
        this.positionCalendar();
    }

    close() {
        this.isOpen = false;
        this.calendar.classList.remove('open');
        this.displayInput.classList.remove('active');
    }

    positionCalendar() {
        const inputRect = this.displayInput.getBoundingClientRect();
        const calendarHeight = 320;
        const spaceBelow = window.innerHeight - inputRect.bottom;
        const spaceAbove = inputRect.top;

        // Posicionar arriba o abajo según espacio disponible
        if (spaceBelow < calendarHeight && spaceAbove > spaceBelow) {
            this.calendar.classList.add('position-top');
            this.calendar.classList.remove('position-bottom');
        } else {
            this.calendar.classList.add('position-bottom');
            this.calendar.classList.remove('position-top');
        }
    }

    render() {
        const year = this.viewDate.getFullYear();
        const month = this.viewDate.getMonth();

        this.calendar.innerHTML = `
            <div class="datepicker-header">
                <button type="button" class="datepicker-nav datepicker-prev-year" title="Año anterior">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="11 17 6 12 11 7"></polyline>
                        <polyline points="18 17 13 12 18 7"></polyline>
                    </svg>
                </button>
                <button type="button" class="datepicker-nav datepicker-prev-month" title="Mes anterior">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="15 18 9 12 15 6"></polyline>
                    </svg>
                </button>
                <div class="datepicker-title">
                    <span class="datepicker-month">${this.t.months[month]}</span>
                    <span class="datepicker-year">${year}</span>
                </div>
                <button type="button" class="datepicker-nav datepicker-next-month" title="Mes siguiente">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                </button>
                <button type="button" class="datepicker-nav datepicker-next-year" title="Año siguiente">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="13 17 18 12 13 7"></polyline>
                        <polyline points="6 17 11 12 6 7"></polyline>
                    </svg>
                </button>
            </div>
            <div class="datepicker-weekdays">
                ${this.t.weekdaysMin.map(d => `<span>${d}</span>`).join('')}
            </div>
            <div class="datepicker-days">
                ${this.renderDays()}
            </div>
            <div class="datepicker-footer">
                <button type="button" class="datepicker-btn datepicker-today">${this.t.today}</button>
                <button type="button" class="datepicker-btn datepicker-clear">${this.t.clear}</button>
            </div>
        `;

        // Event listeners para navegación
        this.calendar.querySelector('.datepicker-prev-year').addEventListener('click', (e) => {
            e.stopPropagation();
            this.changeYear(-1);
        });
        this.calendar.querySelector('.datepicker-next-year').addEventListener('click', (e) => {
            e.stopPropagation();
            this.changeYear(1);
        });
        this.calendar.querySelector('.datepicker-prev-month').addEventListener('click', (e) => {
            e.stopPropagation();
            this.changeMonth(-1);
        });
        this.calendar.querySelector('.datepicker-next-month').addEventListener('click', (e) => {
            e.stopPropagation();
            this.changeMonth(1);
        });

        // Event listeners para días
        this.calendar.querySelectorAll('.datepicker-day:not(.disabled)').forEach(day => {
            day.addEventListener('click', (e) => {
                e.stopPropagation();
                const date = new Date(parseInt(day.dataset.date));
                this.selectDate(date);
            });
        });

        // Botones del footer
        this.calendar.querySelector('.datepicker-today').addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectDate(new Date());
        });
        this.calendar.querySelector('.datepicker-clear').addEventListener('click', (e) => {
            e.stopPropagation();
            this.clearDate();
        });
    }

    renderDays() {
        const year = this.viewDate.getFullYear();
        const month = this.viewDate.getMonth();
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Primer día del mes
        const firstDay = new Date(year, month, 1);
        // Último día del mes
        const lastDay = new Date(year, month + 1, 0);
        // Día de la semana del primer día (0 = Domingo)
        const startWeekday = firstDay.getDay();
        // Total de días en el mes
        const totalDays = lastDay.getDate();

        let days = '';

        // Días del mes anterior (vacíos)
        const prevMonthLastDay = new Date(year, month, 0).getDate();
        for (let i = startWeekday - 1; i >= 0; i--) {
            const day = prevMonthLastDay - i;
            days += `<span class="datepicker-day other-month disabled">${day}</span>`;
        }

        // Días del mes actual
        for (let day = 1; day <= totalDays; day++) {
            const date = new Date(year, month, day);
            date.setHours(0, 0, 0, 0);

            let classes = ['datepicker-day'];

            // Es hoy
            if (date.getTime() === today.getTime()) {
                classes.push('today');
            }

            // Está seleccionado
            if (this.selectedDate && date.getTime() === this.selectedDate.getTime()) {
                classes.push('selected');
            }

            // Verificar min/max date
            let disabled = false;
            if (this.options.minDate && date < this.options.minDate) {
                disabled = true;
            }
            if (this.options.maxDate && date > this.options.maxDate) {
                disabled = true;
            }
            if (disabled) {
                classes.push('disabled');
            }

            days += `<span class="${classes.join(' ')}" data-date="${date.getTime()}">${day}</span>`;
        }

        // Días del mes siguiente (para completar la grilla)
        const remainingDays = 42 - (startWeekday + totalDays); // 6 filas * 7 días = 42
        for (let day = 1; day <= remainingDays; day++) {
            days += `<span class="datepicker-day other-month disabled">${day}</span>`;
        }

        return days;
    }

    changeMonth(delta) {
        this.viewDate.setMonth(this.viewDate.getMonth() + delta);
        this.render();
    }

    changeYear(delta) {
        this.viewDate.setFullYear(this.viewDate.getFullYear() + delta);
        this.render();
    }

    selectDate(date) {
        this.selectedDate = new Date(date);
        this.selectedDate.setHours(0, 0, 0, 0);
        this.viewDate = new Date(this.selectedDate);

        // Actualizar input original
        this.input.value = this.formatDate(this.selectedDate);

        // Actualizar display
        this.displayInput.querySelector('.datepicker-input-text').innerHTML =
            this.formatDisplayDate(this.selectedDate);

        // Disparar evento change
        this.input.dispatchEvent(new Event('change', { bubbles: true }));

        // Callback
        if (this.options.onChange) {
            this.options.onChange(this.selectedDate, this.formatDate(this.selectedDate));
        }

        this.render();
        this.close();
    }

    clearDate() {
        this.selectedDate = null;
        this.viewDate = new Date();
        this.input.value = '';

        this.displayInput.querySelector('.datepicker-input-text').innerHTML =
            this.formatDisplayDate(null);

        // Disparar evento change
        this.input.dispatchEvent(new Event('change', { bubbles: true }));

        // Callback
        if (this.options.onChange) {
            this.options.onChange(null, '');
        }

        this.render();
        this.close();
    }

    formatDate(date) {
        if (!date) return '';
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    formatDisplayDate(date) {
        if (!date) {
            return `<span class="placeholder">${this.t.selectDate}</span>`;
        }
        const day = date.getDate();
        const month = this.t.monthsShort[date.getMonth()];
        const year = date.getFullYear();
        return `${day} ${month} ${year}`;
    }

    setDate(date) {
        if (date) {
            this.selectDate(new Date(date));
        } else {
            this.clearDate();
        }
    }

    getDate() {
        return this.selectedDate;
    }

    getValue() {
        return this.input.value;
    }

    setLocale(locale) {
        this.options.locale = locale;
        this.displayInput.querySelector('.datepicker-input-text').innerHTML =
            this.formatDisplayDate(this.selectedDate);
        this.render();
    }

    destroy() {
        // Restaurar input original
        this.input.type = 'date';
        this.wrapper.parentNode.insertBefore(this.input, this.wrapper);
        this.wrapper.remove();
    }
}

// Función helper para inicializar datepickers
function initDatepickers(selector = 'input[type="date"]', options = {}) {
    const inputs = document.querySelectorAll(selector);
    const instances = [];

    inputs.forEach(input => {
        // Evitar doble inicialización
        if (!input.datepickerInstance) {
            const instance = new Datepicker(input, options);
            input.datepickerInstance = instance;
            instances.push(instance);
        }
    });

    return instances;
}

// Exponer globalmente
window.Datepicker = Datepicker;
window.initDatepickers = initDatepickers;
