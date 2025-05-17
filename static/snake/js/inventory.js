async function getUnlockedItems() {
    const response = await fetch("/api/account/items", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    return await handleJsonResponse(response);
}

async function selectItem(itemId, itemType) {
    const selectedItem = document.querySelectorAll(".item.selected");
    for (const item of selectedItem) {
        if (item.id.replace("item-", "") === itemId) return;
    }

    const response = await fetch(`/api/account/${itemType}/select`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({[itemType]: itemId})
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        const selectedItem = document.querySelectorAll(`#${itemType}s-content .item.selected`);
        for (const item of selectedItem) {
            item.classList.remove("selected");
        }

        const itemElement = document.getElementById(`item-${itemId}`)
        itemElement.classList.add("selected");

        if (itemType === "background") {
            document.querySelector(".container.inventory").style.backgroundImage = `url(${responseJson["path"]})`;
        }
    }
}

async function createUnlockedItemsList() {
    const items = await getUnlockedItems();

    const unlockedItems = items["unlocked_items"];
    const selectedItems = items["selected_items"]

    const skinsList = document.querySelector(`#skins-content .items`);
    const foodSkinsList = document.querySelector(`#food_skins-content .items`);
    const backgroundsList = document.querySelector(`#backgrounds-content .items`);

    skinsList.innerHTML = "";
    backgroundsList.innerHTML = "";

    for (const item of unlockedItems) {
        const itemDiv = `
            <div id="item-${item["item_id"]}" class="item" onclick="selectItem('${item["item_id"]}', '${item["type"]}')">
                <div class="title">${item["name"]}</div>
                <img src="${item["path"]}" alt="${item["path"]}" loading="lazy">
            </div>
        `;

        if (item["type"] === "background") {
            backgroundsList.insertAdjacentHTML('beforeend', itemDiv);
        } else if (item["type"] === "skin"){
            skinsList.insertAdjacentHTML('beforeend', itemDiv);
        } else if (item["type"] === "food_skin") {
            foodSkinsList.insertAdjacentHTML('beforeend', itemDiv);
        }

        if (item["item_id"] === selectedItems[item["type"]]) {
            document.getElementById(`item-${item["item_id"]}`).classList.add("selected");
        }
    }
}


async function openInventoryTab(tabName) {
    if (document.querySelector(`#${tabName}-content`).classList.contains("show")) {
        return;
    }

    document.querySelectorAll('.inventory-section').forEach(section => {
        section.classList.remove('show');
    });

    document.querySelectorAll('.nav-item').forEach(nav => {
        nav.classList.remove('selected');
    });
    document.querySelector(`#${tabName}-nav`).classList.add('selected');

    setTimeout(() => {
        document.querySelectorAll('.inventory-section').forEach(section => {
            section.style.display = 'none';
        });

        const section = document.querySelector(`#${tabName}-content`);
        section.style.display = '';

        setTimeout(() => {
            section.classList.add('show');
        }, 1)
    }, 300)
}

createUnlockedItemsList().then(async function() {
    await openInventoryTab("skins");
});
