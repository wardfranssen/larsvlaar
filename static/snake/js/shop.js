async function getLootBoxes() {
    const response = await fetch(`/api/shop/loot_boxes`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        return responseJson["items"];
    }
}

async function createLootBoxesList() {
    const lootBoxes = await getLootBoxes();

    const lootBoxesList = document.querySelector(`#loot_boxes-content .loot_boxes`);

    lootBoxesList.innerHTML = "";

    for (const lootBox of lootBoxes) {
        const lootBoxDiv = `
            <div id="box-${lootBox["loot_box_id"]}" class="item loot-box">
                <span class="title">${lootBox["name"]}</span>
        
                <div class="preview-box"><div class="preview-upper"></div>
                    <div class="preview-latch"></div>
                    <div class="preview-lower ${lootBox["type"]}-box"></div>
                </div>
                <p class="price">${lootBox["price"]} vlaar coins</p>
                <button class="buy-button" onclick="openLootBox('${lootBox["loot_box_id"]}', '${lootBox["type"]}')"></button>
            </div>
        `;
        lootBoxesList.insertAdjacentHTML('beforeend', lootBoxDiv);
    }
}

createLootBoxesList();


async function openLootBox(id, type) {
    const button = document.querySelector(`.loot_boxes #box-${id} .buy-button`);
    button.classList.add('bought');
    button.disabled = true;

    const response = await fetch(`/api/shop/loot_boxes/${id}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    if (!responseJson) {
        button.classList.remove('bought');
        button.disabled = false;
        return;
    }
    spawnBox(type);

    const item = responseJson["item"]
    const imgPath = item["path"]

    const balanceAmountSpan = document.querySelector(`.balance-amount`);
    const balance = Number(balanceAmountSpan.innerText);
    balanceAmountSpan.innerText = balance - Number(item["price"]);

    const box = document.querySelector('.box');

    // When the player clicks on the box it will open
    box.addEventListener('click', async function() {
        const box = document.querySelector('.box');
        const box_background = document.querySelector('#box-background');


        if (box.classList.contains('opened')) {
            return;
        }
        box.classList.add('opened');

        box.style.backgroundImage = `url(${imgPath})`;

        // The box will shake and the background will change colors
        box_background.style.animation = 'rainbow-animation 0.5s infinite';
        box.style.animation = 'worst_shake 0.8s cubic-bezier(.3,.06,.2,.9) infinite';

        // After 1 second the box will become transparent
        await new Promise(resolve => setTimeout(resolve, 1000));
        document.querySelector('.upper').style.opacity = 0;
        document.querySelector('.lower').style.opacity = 0;
        document.querySelector('.latch').style.opacity = 0;

        // The opening animation is now finished
        setTimeout(function() {
            box.style.borderRadius = '10%';
            box.style.width = '90vh';
            box.style.height = '90vh';
            box.style.animation = 'shake 50s cubic-bezier(.3,.06,.2,.9) infinite';
            box_background.style.animation = 'rainbow-animation 50s infinite';
        }, 350);

        // When the player clicks on the background it will close everything
        box_background.addEventListener('click', async function() {
            // Don't know what this does, but it's needed!
            e = window.event || e;
            if(this !== e.target) {
                return;
            }

            // Allow the user to buy another box
            // And prepare everything for the next box
            const button = document.querySelector(`.loot_boxes #box-${id} .buy-button`);

            button.disabled = false;
            button.classList.remove('bought');

            document.querySelector('.box').remove();
            box_background.style.display = 'none';
            box_background.style.animation = 'rainbow-animation 5s infinite';
            this.removeEventListener('click', arguments.callee);
        });

        this.removeEventListener('click', arguments.callee);
    });
}


function spawnBox(type) {
    const container = document.querySelector('#box-background');
    container.style.display = 'flex';

    const boxDiv = `
        <div class="box">
            <div class="upper"></div>
            <div class="lower ${type}-box"></div>
            <div class="latch"></div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', boxDiv);
}
