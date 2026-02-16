document.addEventListener('DOMContentLoaded', () => {
    const listElement = document.getElementById('valueset-list');
    const contentElement = document.getElementById('content');

    // Fetch and list ValueSets
    async function loadValueSets() {
        try {
            const response = await fetch('/list/valuesets');
            const valuesets = await response.json();

            listElement.innerHTML = '';
            valuesets.forEach(vs => {
                const li = document.createElement('li');
                li.className = 'valueset-item';
                li.textContent = vs.accession;
                li.onclick = () => selectValueSet(vs.accession);
                listElement.appendChild(li);
            });
        } catch (error) {
            listElement.innerHTML = '<li class="error">Failed to load ValueSets</li>';
            console.error(error);
        }
    }

    // Fetch and display terms for a ValueSet
    async function selectValueSet(accession) {
        // Update selection UI
        document.querySelectorAll('.valueset-item').forEach(el => {
            el.classList.toggle('active', el.textContent === accession);
        });

        contentElement.innerHTML = '<p class="loading">Loading terms...</p>';

        try {
            const response = await fetch(`/list/valuesets/${accession}`);
            const data = await response.json();
            renderTerms(data);
        } catch (error) {
            contentElement.innerHTML = '<p class="error">Failed to load terms</p>';
            console.error(error);
        }
    }

    function renderTerms(data) {
        let html = `
            <h2>${data.accession}</h2>
            <p class="description">${data.definition || ''}</p>
            <table>
                <thead>
                    <tr>
                        <th>Accession</th>
                        <th>Label</th>
                        <th>Value</th>
                        <th>Definition</th>
                        <th>Additional Data</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.values.forEach(term => {
            const additionalHtml = term.additional ? Object.entries(term.additional)
                .map(([key, value]) => `
                    <div class="additional-field">
                        <span class="field-key">${key}:</span>
                        <span class="field-value">${typeof value === 'object' ? JSON.stringify(value) : value}</span>
                    </div>
                `).join('') : '';

            html += `
                <tr>
                    <td>
                        ${term.accession}
                        ${term.deprecated ? '<br><span class="deprecated">Deprecated</span>' : ''}
                    </td>
                    <td>${term.label}</td>
                    <td>${term.value}</td>
                    <td>${term.definition || ''}</td>
                    <td>${additionalHtml}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        contentElement.innerHTML = html;
    }

    loadValueSets();
});
