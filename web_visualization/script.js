const ANIMATION_DELAY = 2500; // Задержка между анимациями
const FADE_OUT_DELAY = 600; // Задержка исчезновения элементов
const SCALE_UP_DELAY = 100; // Задержка увеличения нового элемента
const SCALE_DOWN_DELAY = 200; // Задержка уменьшения нового элемента

async function fetchDataFromClickHouse() {
    const clickhouse_server_url = 'http://127.0.0.1:8123/?query=SELECT%20*%20FROM%20system.part_log%20FORMAT%20JSON';

    try {
        const response = await fetch(clickhouse_server_url);

        if (!response.ok) {
            throw new Error('Ошибка загрузки данных с ClickHouse');
        }

        const result = await response.json();
        const data = result.data;

        // Сортируем данные по времени и фильтруем данные
        const filtered_data = data
            .filter(part => part.event_type !== 'RemovePart')
            .sort((a, b) => new Date(a.event_time) - new Date(b.event_time));

        filtered_data.forEach(part => {
            part.size_in_bytes = parseInt(part.size_in_bytes, 10);
        });

        return filtered_data;
    } catch (error) {
        updateActionText(`Ошибка: ${error.message}`);
        console.error('Ошибка при загрузке данных:', error);
        throw error;
    }
}

function updateActionText(message) {
    document.getElementById('action_text').textContent = message;
}


function createNewPart(part, total_size) {
    const new_part = document.createElement('div');
    new_part.classList.add('part');

    if (part.event_type === 'MergeParts') {
        new_part.style.backgroundColor = '#ff5733'
        new_part.classList.add('merged');
    } else {
        new_part.style.backgroundColor = '#3333ff'
    }
    new_part.style.height = (part.size_in_bytes / total_size * 150) + '%';
    new_part.setAttribute('data-name', part.part_name);

    new_part.innerHTML = `
        <span style="margin-bottom: 5px;">${part.part_name}</span>
        <span style="font-size: 14px;">${(part.size_in_bytes / (1024 * 1024)).toFixed(2)} MB</span>
    `;

    return new_part;
}

function handleNewPartAnimation(part, total_size, visualization, current_parts) {
    updateActionText(`Добавление нового куска: ${part.part_name}`);
    const new_part = createNewPart(part, total_size);
    current_parts.push(part);
    visualization.appendChild(new_part);
}

function fadeOutParts(parts) {
    parts.forEach(part => {
        part.style.opacity = '0';
    });
}

function removeMergedParts(merged_parts, current_parts, mergedFrom) {
    merged_parts.forEach(partEl => partEl.remove());
    current_parts = current_parts.filter(part => !mergedFrom.includes(part.part_name));
}

function scaleAndFadeInPart(part) {
    setTimeout(() => {
        part.style.transform = 'scale(1.05)';
        part.style.opacity = '1';

        setTimeout(() => {
            part.style.transform = 'scale(1)';
        }, SCALE_DOWN_DELAY);
    }, SCALE_UP_DELAY);
}

function handleMergeAnimation(part, visualization, current_parts) {
    updateActionText(`Начало слияния: ${part.merged_from.join(' + ')} → ${part.part_name}`);

    // Все элементы, участвующие в слиянии
    const merged_parts = part.merged_from.map(mergedPartName => document.querySelector(`.part[data-name="${mergedPartName}"]`));

    const all_positions = merged_parts.map(partEl => partEl.offsetLeft);
    const center_position = all_positions.reduce((a, b) => a + b, 0) / merged_parts.length;

    // Анимация перемещения частей к центральной позиции
    merged_parts.forEach((partEl, index) => {
        partEl.style.transform = `translateX(${center_position - all_positions[index]}px)`;
    });

    setTimeout(() => {
        updateActionText(`Слияние завершено: ${part.merged_from.join(' + ')} → ${part.part_name}`);
        fadeOutParts(merged_parts);

        setTimeout(() => {
            removeMergedParts(merged_parts, current_parts, part.merged_from);

            // Пересчитываем общий размер всех оставшихся частей
            const new_total_size = current_parts.reduce((acc, p) => acc + p.size_in_bytes, part.size_in_bytes);
            const merged_part = createNewPart(part, new_total_size);
            merged_part.style.transform = 'scale(0.8)';
            merged_part.style.opacity = '0';
            visualization.appendChild(merged_part);

            scaleAndFadeInPart(merged_part);

        }, FADE_OUT_DELAY);
    }, FADE_OUT_DELAY);
}

function visualizeParts(parts) {
    const visualization = document.getElementById('visualization');
    visualization.innerHTML = '';

    // Вычисляем общий размер всех частей
    const total_size = parts.reduce((acc, part) => acc + part.size_in_bytes, 0);
    let current_parts = [];
    let animation_index = 0;

    function animate() {
        if (animation_index >= parts.length) {
            updateActionText("Визуализация завершена.");
            return;
        }

        const current_part = parts[animation_index];

        if (current_part.event_type === 'NewPart') {
            handleNewPartAnimation(current_part, total_size, visualization, current_parts);
        } else if (current_part.event_type === 'MergeParts') {
            handleMergeAnimation(current_part, visualization, current_parts);
        }

        ++animation_index;
        setTimeout(animate, ANIMATION_DELAY);
    }

    animate();
}

document.getElementById('start').addEventListener('click', () => {
    fetchDataFromClickHouse().then(data => {
        visualizeParts(data);
    });
});

document.getElementById('reset').addEventListener('click', () => {
    document.getElementById('visualization').innerHTML = '';
    updateActionText("Нажмите 'Старт', чтобы начать визуализацию");
});
