
function DependencySelectAjax(url, target_id, selected_ids=[]) {
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // clean the target select field
            $(`#${target_id}`).empty();

            // add options to the target select field
            $.each(data.results, function(index, value) {
                $(`#${target_id}`).append($('<option>', {
                    value: value.id,
                    text: value.display,
                    selected: selected_ids.includes(value.id),
                }));
            });
        })
        .catch(error => console.error('Error:', error));
}

// --- Drag and Drop functions start ---
// function IsBefore(a, b) {
//     if (a.parentNode == b.parentNode) {
//         for (var cur = a; cur; cur = cur.previousSibling) {
//             if (cur === b) {
//                 return true;
//             }
//         }
//     }
//     return false;
// }

// function DragEnter(e) {
//     var targetelem = e.target;
//     if (targetelem.nodeName == "TD") {
//        targetelem = targetelem.parentNode;   
//     }  

//     if (IsBefore(source, targetelem)) {
//         targetelem.parentNode.insertBefore(source, targetelem);
//     } else {
//         targetelem.parentNode.insertBefore(source, targetelem.nextSibling);
//     }
// }

// function DragStart(e) {
//     source = e.target;
//     e.dataTransfer.effectAllowed = 'move';
// }
// --- Drag and Drop functions end ---