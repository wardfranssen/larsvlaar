async function buyItem(itemId, category) {
    let button = document.querySelector(`#shop_page .${category} .items #${itemId} button`);
    button.disabled = true;
    button.innerHTML = '✔';

    const response = await fetch (`/buy/${category}/${itemId}`, {
        method: "POST"
    })

    const text = await response.text();

    if (text.includes('Error: ') || response.status === 429) {
        button.disabled = false;
        button.innerHTML = 'Buy';
        let error = '';

        if (response.status === 429) {
            error = 'Please wait a few seconds before buying again';
        } else {
            error = text.split('Error: ')[1];
        }

        let dangerAlerts = document.getElementsByClassName('alert-danger');
        if (dangerAlerts.length > 0) {
            if (vibrateAlreadyExistingAlert(dangerAlerts, error)) {
                return;
            }
        }
        deletePopupsByCategory('danger');
        createPopup(error, 'danger', `${itemId}-messages-${category}`);
    } else {
        deletePopupsByCategory('danger');
        const coinsVal = document.querySelector('.coinsVal');
        coinsVal.innerHTML = text;
        
        return;
    }   
}


async function onLoadShop(){
    // This function is called when the shop page is loaded


    // Fetching the backgrounds, skins and pipeskins from the server
    let backgrounds = await fetch('/backgrounds');
    backgrounds = JSON.parse(await backgrounds.text());

    let skins = await fetch('/skins');
    skins = JSON.parse(await skins.text());

    let pipeskins = await fetch('/pipeskins');
    pipeskins = JSON.parse(await pipeskins.text());

    // Couldn't find a way to create the html element inside the js
    // So I had to fetch the html from the server
    let message = await fetch('/get_flashed_messages');
    message = JSON.parse(await message.text()).html;

    // Array to store the items that are not for sale(items that are in db with price -1)
    let notForSale = []

    // The next 3 for loops are for creating the items in the shop
    // I know that I could maybe do this in a more efficient way(nested for loops), but I'm lazy
    for (i = 0; i < backgrounds.length; i++) {
        if (backgrounds[i][1] == -1) {
            notForSale.push(backgrounds[i][0]);
            continue;
        }
        const parent = document.querySelector(`#shop_page .backgrounds .items`);

        let element = document.createElement('div');
        element.className = 'item';
        element.id = backgrounds[i][0];
        parent.appendChild(element);

        // Creating the image element
        let img = document.createElement('img');
        img.src = `/img/shop/${backgrounds[i][0]}.jpg`;
        img.classList.add('backgroundItem');
        img.loading = 'lazy';
        element.appendChild(img);

        // Creating the span element, this is the name of the item
        let span = document.createElement('span');
        span.innerHTML = camelCaseToSpaces(backgrounds[i][0]);
        element.appendChild(span);

        // Creating the p element, this is the price of the item
        let p = document.createElement('p');
        p.innerHTML = `Cost: ${backgrounds[i][1]} coins`;
        element.appendChild(p);

        // Creating the buy button
        let button = document.createElement('button');
        button.classList.add('buyButton');
        button.innerHTML = 'Buy';
        button.onclick = (function(item) {
            return function() {
                buyItem(item[0], 'backgrounds');
            };
        })(backgrounds[i]);
        element.appendChild(button);

        // Creating the messages div, this is where errors will be displayed
        let messages = document.createElement('div');
        messages.id = `${backgrounds[i][0]}-messages-backgrounds`;
        messages.innerHTML = message;
        element.appendChild(messages);
    }

    for (i = 0; i < skins.length; i++) {
        if (skins[i][1] == -1) {
            notForSale.push(skins[i][0]);
            continue;
        }
        const parent = document.querySelector(`#shop_page .skins .items`);

        let element = document.createElement('div');
        element.className = 'item';
        element.id = skins[i][0];
        parent.appendChild(element);

        let img = document.createElement('img');
        img.src = `/img/shop/${skins[i][0]}.jpg`;
        img.classList.add('backgroundItem');
        img.loading = 'lazy';
        element.appendChild(img);

        let span = document.createElement('span');
        span.innerHTML = camelCaseToSpaces(skins[i][0]);
        element.appendChild(span);

        let p = document.createElement('p');
        p.innerHTML = `Cost: ${skins[i][1]} coins`;
        element.appendChild(p);

        let button = document.createElement('button');
        button.classList.add('buyButton');
        button.innerHTML = 'Buy';
        button.onclick = (function(item) {
            return function() {
                buyItem(item[0], 'skins');
            };
        })(skins[i]);
        element.appendChild(button);

        let messages = document.createElement('div');
        messages.id = `${skins[i][0]}-messages-skins`;
        messages.innerHTML = message;
        element.appendChild(messages);
    }

    for (i = 0; i < pipeskins.length; i++) {
        if (pipeskins[i][1] == -1) {
            notForSale.push(pipeskins[i][0]);
            continue;
        }
        const parent = document.querySelector(`#shop_page .pipeskins .items`);

        let element = document.createElement('div');
        element.className = 'item';
        element.id = pipeskins[i][0];
        parent.appendChild(element);

        let img = document.createElement('img');
        if (pipeskins[i][0] == 'greenPipe') {
            img.src = `/img/shop/greenPipe.png`;
        } else {
            img.src = `/img/shop/${pipeskins[i][0]}.jpg`;
        }
        img.classList.add('backgroundItem');
        img.loading = 'lazy';
        element.appendChild(img);

        let span = document.createElement('span');
        span.innerHTML = camelCaseToSpaces(pipeskins[i][0]);
        element.appendChild(span);

        let p = document.createElement('p');
        p.innerHTML = `Cost: ${pipeskins[i][1]} coins`;
        element.appendChild(p);

        let button = document.createElement('button');
        button.classList.add('buyButton');
        button.innerHTML = 'Buy';
        button.onclick = (function(item) {
            return function() {
                buyItem(item[0], 'pipeskins');
            };
        })(pipeskins[i]);
        element.appendChild(button);

        let messages = document.createElement('div');
        messages.id = `${pipeskins[i][0]}-messages-pipeskins`;
        messages.innerHTML = message;
        element.appendChild(messages);
    }

    // Fetching the items that the player has unlocked from the server
    let response = await fetch ("/unlocked", {
        method: "GET"
    });

    let unlockedItems = await response.text();
    let unlockedSkins = JSON.parse(unlockedItems).skins;
    let unlockedBackgrounds = JSON.parse(unlockedItems).backgrounds;
    let unlockedPipeskins = JSON.parse(unlockedItems).pipeskins;

    // Disabling the buy buttons for the items that the player has already unlocked
    for (let i = 0; i < unlockedSkins.length; i++) {
        if (notForSale.includes(unlockedSkins[i])) {
            continue;
        }
        console.log(unlockedSkins[i]);
        let button = document.querySelector(`#shop_page .skins .items #${unlockedSkins[i]} button`);
        button.disabled = true;
        button.innerHTML = '✔';
    }
    
    for (let i = 0; i < unlockedBackgrounds.length; i++) {
        console.log(unlockedBackgrounds[i]);
        if (notForSale.includes(unlockedBackgrounds[i])) {
            continue;
        }
        let button = document.querySelector(`#shop_page .backgrounds .items #${unlockedBackgrounds[i]} button`);
        button.disabled = true;
        button.innerHTML = '✔';
    }

    for (let i = 0; i < unlockedPipeskins.length; i++) {
        if (notForSale.includes(unlockedPipeskins[i])) {
            continue;
        }
        let button = document.querySelector(`#shop_page .pipeskins .items #${unlockedPipeskins[i]} button`);
        button.disabled = true;
        button.innerHTML = '✔';
    }

    shopOpenBackgrounds();
    loadLootboxesPage(message);
}


function shopOpenBackgrounds() {
    // This function is called when the player clicks on the backgrounds link in the shop
    document.querySelector('#shop_page .pipeskins').style.display = 'none';
    document.querySelector('#shop_page .skins').style.display = 'none';
    document.querySelector('#shop_page .lootboxes').style.display = 'none';
    document.querySelector('#shop_page .backgrounds').style.display = 'block';

    const navlinks = document.querySelectorAll('#shop_page .nav .navlink');

    for (let i = 0; i < navlinks.length; i++) {
        if (navlinks[i].innerHTML != 'Backgrounds') {
            navlinks[i].classList.remove('selectedLink');
        } else {
            navlinks[i].classList.add('selectedLink');
        }
    }
}

function shopOpenSkins() {
    // This function is called when the player clicks on the skins link in the shop
    document.querySelector('#shop_page .backgrounds').style.display = 'none';
    document.querySelector('#shop_page .pipeskins').style.display = 'none';
    document.querySelector('#shop_page .lootboxes').style.display = 'none';
    document.querySelector('#shop_page .skins').style.display = 'block';

    const navlinks = document.querySelectorAll('#shop_page .nav .navlink');

    for (let i = 0; i < navlinks.length; i++) {
        if (navlinks[i].innerHTML != 'Skins') {
            navlinks[i].classList.remove('selectedLink');
        } else {
            navlinks[i].classList.add('selectedLink');
        }
    }
}

function shopOpenPipeskins() {
    // This function is called when the player clicks on the pipeskins link in the shop
    document.querySelector('#shop_page .backgrounds').style.display = 'none';
    document.querySelector('#shop_page .skins').style.display = 'none';
    document.querySelector('#shop_page .lootboxes').style.display = 'none';
    document.querySelector('#shop_page .pipeskins').style.display = 'block';

    const navlinks = document.querySelectorAll('#shop_page .nav .navlink');

    for (let i = 0; i < navlinks.length; i++) {
        if (navlinks[i].innerHTML != 'Pipeskins') {
            navlinks[i].classList.remove('selectedLink');
        } else {
            navlinks[i].classList.add('selectedLink');
        }
    }
}

function shopOpenLootBoxes() {
    // This function is called when the player clicks on the loot boxes link in the shop
    document.querySelector('#shop_page .backgrounds').style.display = 'none';
    document.querySelector('#shop_page .skins').style.display = 'none';
    document.querySelector('#shop_page .pipeskins').style.display = 'none';
    document.querySelector('#shop_page .lootboxes').style.display = 'block';

    const navlinks = document.querySelectorAll('#shop_page .nav .navlink');

    for (let i = 0; i < navlinks.length; i++) {
        if (navlinks[i].innerHTML != 'Loot boxes') {
            navlinks[i].classList.remove('selectedLink');
        } else {
            navlinks[i].classList.add('selectedLink');
        }
    }    
}

async function loadLootboxesPage(message) {
    const response = await fetch('/get_lootboxes');

    const text = await response.text();

    const lootboxes = JSON.parse(text);
    
    for (let i = 0; i < lootboxes.length; i++) {
        const parent = document.querySelector(`#shop_page .lootboxes .items`);

        let element = document.createElement('div');
        element.className = 'item';
        element.id = lootboxes[i].name;
        parent.appendChild(element);

        // Creating the image element, which isn't an image, but a div
        let img = document.createElement('div');
        img.classList.add('previewBox');
        element.appendChild(img);

        let upper = document.createElement('div');
        upper.classList.add('previewUpper');
        img.appendChild(upper);

        let latch = document.createElement('div');
        latch.classList.add('previewLatch');
        img.appendChild(latch);
        
        let lower = document.createElement('div');
        lower.classList.add('previewLower');
        lower.classList.add(`${lootboxes[i].name}Lower`);
        img.appendChild(lower);

        // Creating the name of the box
        let span = document.createElement('span');
        span.innerHTML = camelCaseToSpaces(lootboxes[i].name);
        element.appendChild(span);

        // Creating the price of the box
        let p = document.createElement('p');
        p.innerHTML = `Cost: ${lootboxes[i].price} coins`;
        element.appendChild(p);

        // Creating the buy button
        let button = document.createElement('button');
        button.classList.add('buyButton');
        button.innerHTML = 'Buy';
        button.onclick = (function(item) {
            return function() {
                openALootbox(item.name);
            };
        })(lootboxes[i]);
        element.appendChild(button);

        // This is the little info icon that shows the odds of the lootbox
        let openInfo = document.createElement('div');
        // openInfo.style.backgroundImage = `/img/infoIcon.svg`;
        openInfo.classList.add('openInfo');

        // On hover the info will be displayed
        openInfo.addEventListener("mouseover", (function() {
            return function() {
                const info = document.querySelector(`#${lootboxes[i].name}`).getElementsByClassName("info")[0];
                info.style.display = "block";
            };
        })());

        // When mouse is not hovering over the info icon the info will be hidden
        openInfo.addEventListener("mouseout", (function() {
            return function() {
                const info = document.querySelector(`#${lootboxes[i].name}`).getElementsByClassName("info")[0];
                info.style.display = "none";
            };
        })());

        element.appendChild(openInfo);

        // Creating the div that accually contains the odds of the lootbox
        CreateInfoElement(lootboxes[i]);

        // Creating the messages div, this is where errors will be displayed
        let messages = document.createElement('div');
        messages.id = `${lootboxes[i].name}-messages-lootboxes`;
        messages.innerHTML = message;
        element.appendChild(messages);
    }
}


function CreateInfoElement(item){
    // This function creates the div that contains the odds of the lootbox

    const info = document.createElement("div");
    info.classList.add("info");
    info.style.right = "70%";
    document.querySelector(`#${item.name} .openInfo`).appendChild(info);

    // On mouse hover the info will be displayed
    info.addEventListener("mouseover", (function() {
        return function() {
            // const info = document.getElementById(`${username}armor${i}`).getElementsByClassName("info")[0];
            info.style.display = "block";
        };
    })());

    // If not hovering over the info it will be hidden
    info.addEventListener("mouseout", (function() {
        return function() {
            // const info = document.getElementById(`${username}armor${i}`).getElementsByClassName("info")[0];
            info.style.display = "none";
        };
    })());

    // The actual text that will be displayed
    infoText = document.createElement("p");
    const odds = JSON.parse(item.odds);
    const keys = Object.keys(odds);
    
    infoText.innerHTML = `Odds:<br>`;

    // Looping through the odds and displaying them
    // The odds are in the format of "numerator/denominator"
    // The percentage is calculated by dividing the numerator by the denominator and multiplying by 100 to get a percentage
    for (let i = 0; i < Object.keys(odds).length; i++) {
        const [numerator, denominator] = odds[keys[i]].split('/').map(Number);
        const percentage = (numerator / denominator) * 100;
        const name = keys[i].replace(/_/g, ' ').replace('backgrounds', 'background').replace('skins', 'skin').replace('pipeskins', 'pipeskin');
        infoText.innerHTML += `${name}: ${percentage}%<br>`;
    }
    info.appendChild(infoText);

    return info;
}


async function openALootbox(id) {
    // This function is called when the player clicks on the buy button of a lootbox

    // Disabling the button so the player can't buy the lootbox multiple times
    let button = document.querySelector(`#shop_page .lootboxes .items #${id} button`);
    button.disabled = true;
    button.innerHTML = '✔';

    // Tell the server that we want to open a box
    // This request will return the item that the player has won
    const response = await fetch(`/open_lootbox/${id}`, {
        method: "POST"
    });

    const text = await response.text();

    // If the server returns an error we will display it
    if (text.includes('Error: ') || response.status === 429) {
        button.disabled = false;
        button.innerHTML = 'Buy';
        let error = '';


        if (response.status === 429) {
            error = 'Please wait a few seconds before buying again';
        } else {
            error = text.split('Error: ')[1].replace('"}', "");
        }

        let dangerAlerts = document.getElementsByClassName('alert-danger');
        if (dangerAlerts.length > 0) {
            if (vibrateAlreadyExistingAlert(dangerAlerts, error)) {
                return;
            }
        }
        deletePopupsByCategory('danger');
        createPopup(error, 'danger', `${id}-messages-lootboxes`);
        return;
    }

    deletePopupsByCategory('danger');

    // Start the animation by spawning the box
    spawnBox(id);

    // Parse the item and the price from the response
    const item = JSON.parse(text).winner;
    const price = JSON.parse(text).price;

    // Update the coins value
    const coinsVal = document.querySelector('.coinsVal');
    coinsVal.innerHTML = parseInt(coinsVal.innerHTML) - price;

    const box = document.querySelector('.box');

    // When the player clicks on the box it will open
    box.addEventListener('click', async function() {
        const box = document.querySelector('.box');
        const box_background = document.querySelector('#box_background');


        if (box.classList.contains('opened')) {
            return;
        }
        box.classList.add('opened');

        // If the item is coins we will display the coins image
        // Else we will display the image of the item
        if (item.includes('coins')) {
            box.style.backgroundImage = `url(/img/coins.png)`;
            coinsVal.innerHTML = parseInt(coinsVal.innerHTML) + Number(item.split(' ')[0]);
        } else{
            box.style.backgroundImage = `url(/img/unlocked/${item}.jpg)`;

        }

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
        }, 400);

        // When the player clicks on the background it will close everything
        box_background.addEventListener('click', async function() {
            // Don't know what this does, but it's needed!
            e = window.event || e; 
            if(this !== e.target) {
                return;
            }

            // Allow the user to buy another box
            // And prepare everything for the next box
            let button = document.querySelector(`#shop_page .lootboxes .items #${id} button`);
            button.disabled = false;
            button.innerHTML = 'Buy';
            document.querySelector('.box').remove();
            box_background.style.display = 'none';
            box_background.style.animation = 'rainbow-animation 5s infinite';
            this.removeEventListener('click', arguments.callee);
        });

        this.removeEventListener('click', arguments.callee);
    });   
}


function spawnBox(id) {
    // This function creates the box that will be opened when the player buys a lootbox
    const container = document.querySelector('#box_background');
    container.style.display = 'flex';
    const box = document.createElement('div');
    box.classList.add('box');
    container.appendChild(box);

    const upper = document.createElement('div');
    upper.classList.add('upper');
    box.appendChild(upper);

    const lower = document.createElement('div');
    lower.classList.add('lower');
    lower.classList.add(`${id}Lower`);
    box.appendChild(lower);

    const latch = document.createElement('div');
    latch.classList.add('latch');
    box.appendChild(latch);
}