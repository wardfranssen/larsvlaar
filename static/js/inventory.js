async function onLoadInventory(){
    // Get the items that the user has unlocked
    let response = await fetch ("/unlocked", {
        method: "GET"
    });

    let unlockedItems = await response.text();
    skins = JSON.parse(unlockedItems).skins;
    backgrounds = JSON.parse(unlockedItems).backgrounds;
    pipeskins = JSON.parse(unlockedItems).pipeskins;

    // Create all the items in the inventory
    // This is basically the same as the code as in the shop.js file
    // The difference is that you don't need a buy button here
    for (let i = 0; i < backgrounds.length; i++) {
        if (document.querySelector(`#${backgrounds[i]}.background`)) {
            continue;
        }
        let element = document.createElement('div');
        element.className = 'inventoryItem background';
        element.id = backgrounds[i];
        element.onclick = function() { selectBackground(backgrounds[i]); };

        document.querySelector('.backgrounds .inventory').appendChild(element);

        let img = document.createElement('img');
        img.src = `/img/unlocked/${backgrounds[i]}.jpg`;
        img.classList.add('backgroundItem');
        element.appendChild(img);

        let span = document.createElement('span');
        span.innerHTML = camelCaseToSpaces(backgrounds[i]);
        element.appendChild(span);
    }

    for (let i = 0; i < skins.length; i++) {
        if (document.querySelector(`#${skins[i]}.skin`)) {
            continue;
        }
        let element = document.createElement('div');
        element.className = 'inventoryItem skin';
        element.id = skins[i];
        element.onclick = function() { selectSkin(skins[i]); };

        document.querySelector('.skins .inventory').appendChild(element);

        let img = document.createElement('img');
        img.src = `/img/unlocked/${skins[i]}.jpg`;
        img.classList.add('backgroundItem');
        element.appendChild(img);

        let span = document.createElement('span');
        span.innerHTML = camelCaseToSpaces(skins[i]);
        element.appendChild(span);
    }

    for (let i = 0; i < pipeskins.length; i++) {
        if (document.querySelector(`#${pipeskins[i]}.pipeskin`)) {
            continue;
        }
        let element = document.createElement('div');
        element.className = 'inventoryItem pipeskin';
        element.id = pipeskins[i];
        element.onclick = function() { selectPipeskin(pipeskins[i]); };

        document.querySelector('.pipeskins .inventory').appendChild(element);

        let img = document.createElement('img');
        if (pipeskins[i] == 'greenPipe') {
            img.src = `/img/unlocked/greenPipe.png`;
        } else {
            img.src = `/img/unlocked/${pipeskins[i]}.jpg`;
        }
        img.classList.add('backgroundItem');
        element.appendChild(img);

        let span = document.createElement('span');
        span.innerHTML = camelCaseToSpaces(pipeskins[i]);
        element.appendChild(span);
    }

    // Set the button for the pipeskin mode
    let currentMode = localStorage.getItem('pipeskinMode');
    let button = document.querySelector('#togglePipeskinMode');
    if (currentMode == 'cover') {
        button.textContent = 'Toggle Pipe Skin Mode: cover';
    } else if (currentMode == 'contain') {
        button.textContent = 'Toggle Pipe Skin Mode: contain';
    } else if (currentMode == '100%') {
        button.textContent = 'Toggle Pipe Skin Mode: 100%';
    }

    // Set the selected items
    selectBackground(localStorage.getItem('background'));
    selectSkin(localStorage.getItem('skin'));
    selectPipeskin(localStorage.getItem('pipeskin'));
    inventoryOpenBackgrounds();
}


function selectSkin(itemId) {
    // This function is called when the user clicks on a skin in the inventory
    // It will set the selected skin to the one that the user clicked on
    const element = document.querySelector(`.skins .inventory #${itemId}`);
    const selected = document.querySelectorAll('.selected.skin');
    for (let i = 0; i < selected.length; i++) {
        selected[i].classList.remove('selected');
    }
    
    element.classList.add('selected');

    document.querySelector('.bird').src = `/img/unlocked/${itemId}.jpg`;
    document.querySelector('.bird').style.aspectRatio = '1/1';
    localStorage.setItem('skin', itemId);
}


function selectBackground(itemId) {
    // This function is called when the user clicks on a background in the inventory
    // It will set the selected background to the one that the user clicked on
    const element = document.querySelector(`.backgrounds .inventory #${itemId}`);
    const selected = document.querySelectorAll('.selected.background');
    for (let i = 0; i < selected.length; i++) {
        selected[i].classList.remove('selected');
    }
    
    element.classList.add('selected');

    document.querySelector('#background').style.backgroundImage = `url(/img/unlocked/${itemId}.jpg)`;
    localStorage.setItem('background', itemId);
}

function selectPipeskin(itemId) {
    // This function is called when the user clicks on a pipeskin in the inventory
    // It will set the selected pipeskin to the one that the user clicked on
    const element = document.querySelector(`.pipeskins .inventory #${itemId}`);
    const selected = document.querySelectorAll('.selected.pipeskin');
    for (let i = 0; i < selected.length; i++) {
        selected[i].classList.remove('selected');
    }
    element.classList.add('selected');

    localStorage.setItem('pipeskin', itemId);
}

function inventoryOpenBackgrounds() {
    // Open the backgrounds section of the inventory
    unlockedItems = document.querySelectorAll('.backgrounds .inventoryItem').length;
    const inventory = document.querySelector('.backgrounds .inventory');
    if (unlockedItems > 3) {
        inventory.style.minWidth = '870px';
        inventory.style.flexWrap = 'wrap';
    } else {
        inventory.style.minWidth = '0px';
        inventory.style.flexWrap = 'nowrap';
    }
    document.querySelector('.skins').style.display = 'none';
    document.querySelector('.pipeskins').style.display = 'none';
    document.querySelector('.backgrounds').style.display = 'block';

    const navlinks = document.querySelectorAll('.nav .navlink');

    for (let i = 0; i < navlinks.length; i++) {
        if (navlinks[i].innerHTML != 'Backgrounds') {
            navlinks[i].classList.remove('selectedLink');
        } else {
            navlinks[i].classList.add('selectedLink');
        }
    }
}

function inventoryOpenSkins() {
    // Open the skins section of the inventory
    const unlockedItems = document.querySelectorAll('.skins .inventoryItem').length;
    const inventory = document.querySelector('.skins .inventory');
    if (unlockedItems > 3) {
        inventory.style.minWidth = '870px';
        inventory.style.flexWrap = 'wrap';
    } else {
        inventory.style.minWidth = '0px';
        inventory.style.flexWrap = 'nowrap';
    }

    document.querySelector('.backgrounds').style.display = 'none';
    document.querySelector('.pipeskins').style.display = 'none';
    document.querySelector('.skins').style.display = 'block';

    const navlinks = document.querySelectorAll('.nav .navlink');


    for (let i = 0; i < navlinks.length; i++) {
        if (navlinks[i].innerHTML != 'Skins') {
            navlinks[i].classList.remove('selectedLink');
        } else {
            navlinks[i].classList.add('selectedLink');
        }
    }
}

function inventoryOpenPipeskins() {
    // Open the pipeskins section of the inventory
    const unlockedItems = document.querySelectorAll('.pipeskins .inventoryItem').length;
    const inventory = document.querySelector('.pipeskins .inventory');
    if (unlockedItems > 3) {
        inventory.style.minWidth = '870px';
        inventory.style.flexWrap = 'wrap';
    } else {
        inventory.style.minWidth = '0px';
        inventory.style.flexWrap = 'nowrap';
    }

    document.querySelector('.skins').style.display = 'none';
    document.querySelector('.backgrounds').style.display = 'none';
    document.querySelector('.pipeskins').style.display = 'block';

    const navlinks = document.querySelectorAll('.nav .navlink');

    for (let i = 0; i < navlinks.length; i++) {
        if (navlinks[i].innerHTML != 'Pipeskins') {
            navlinks[i].classList.remove('selectedLink');
        } else {
            navlinks[i].classList.add('selectedLink');
        }
    }
}

function togglePipeskinMode() {
    // Switch between the different pipeskin modes
    let currentMode = localStorage.getItem('pipeskinMode');
    let button = document.querySelector('#togglePipeskinMode');

    if (currentMode == 'cover') {
        localStorage.setItem('pipeskinMode', 'contain');
        button.textContent = 'Toggle Pipe Skin Mode: contain';
    } else if (currentMode == 'contain') {
        localStorage.setItem('pipeskinMode', '100%');
        button.textContent = 'Toggle Pipe Skin Mode: 100%';
    } else if (currentMode == '100%') {
        localStorage.setItem('pipeskinMode', 'cover');
        button.textContent = 'Toggle Pipe Skin Mode: cover';
    }
}

async function refund() {
    // Send a POST request to the server to refund the user's items and then reload the page
    const response = await fetch ("/refund", {
        method: "POST"});

    if (response.status == 429) {
        alert('You can only refund once every 10 minutes')
        return;
    }
    location.reload();
}