// set all the global stuff
let ip;
let alertTime = 2;
let adminPass = "";
const ERR_NO_ADMIN = 401;
const VALID_FILE_EXT = ["mp3","flac","wav"];

const params = new URLSearchParams(location.search);

let darkmodetemp = getCookie("darkmode");
if(darkmodetemp === "") {
    darkmodetemp = params.get("darkmode")
}
if (darkmodetemp === "true") {
    // i know this is gonna cause weird blinking
    // maybe the dark mode function should be loaded before any content, would that work?
    // NEW JS FILE ????? exciting stuff
    // im thinking a few new js files
    // you know like good design separating stuff
    // yeah but i need the getCookie function in both the darkmode.js and this one, so im gonna make a 
    // getcookie.js
    toggleDark("None");
}

async function alertText(text="Song Added!") {
    alertbox = document.getElementById("alert");
    alertbox.innerHTML = text;
    await new Promise(r => setTimeout(r, alertTime*1000));
    if (alertbox.innerHTML == text) {
        alertbox.innerHTML = ""
    }
}
// a lot of this is kinda waffly because i was trying to get 
// it to return the right stuff and javascript is asyrcronouse (boo)
async function getFromServer(bodyInfo, source="",password=adminPass) {
    try{
        if (bodyInfo != null) {
            // the currently set password is always included in every request
            bodyInfo["password"] = password;
        }
        // console.log(bodyInfo);
        const response = await fetch("http://"+ip+"/"+source, {
            method: "POST",
            body: JSON.stringify(bodyInfo),
            headers: {
                "Content-type": "application/json; charset=UTF-8"
            }
            });
        
        const data = await response.json();
        if (response.status == ERR_NO_ADMIN) {
            // im suprised i didn't comment on this already but this is kinda lame desing
            // its not wrong but you know
            // it is easy which i like
            // and it overrides any other non-async alerts which is nice
            alertText("Error: Admin restricted action")
        } else if(response.status !== 200){
            alertText("Error: "+data.error);
        }
        data["status"] = response.status;
        return await data;
    } catch(e) {
        console.log("error print here:");
        console.log(e);
        if (e == "TypeError: Failed to fetch"){
            alertText("Error: Can't Connect to Server (is the ip set?)")
        } else {
            alertText("Error: " + e);
        }
        const response=null;
        return response;
    }
}

//cookie reader is taken from internet because cookies ae too complicated for me
//i still understand how it works though promise just i see no reason to write this from scratch
function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for(let i = 0; i <ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) == ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(name) == 0) {
        return c.substring(name.length, c.length);
      }
    }
    return "";
    }
//someone more organised than me would have set all these html elements to variables so they dont have to get them 50 times
// also someone who likes things not being dumb more than me would have separated the client and server buttons
let timer = null;
async function controlButton(buttonType) {
    if (buttonType == "pp") { // Play-Pause button
        getFromServer({control: "play-pause"}, "controls")
    } else if (buttonType == "sk") { // Skip button
        getFromServer({control: "skip"}, "controls")
        if (document.getElementById("playlist-mode").style.display == "block") {
            generateVisualPlaylist("skip-button");
        }
    } else if (buttonType == "pl") { // Playlist button
        document.getElementById("songlist").innerHTML = "";
        document.getElementById("playlist").innerHTML = "<h1 id=\"playlist-alert\"></h1>";
        document.getElementById("playlist-mode").style.display = "block";
        document.getElementById("songlist-mode").style.display = "none";
        document.getElementById("settings-mode").style.display = "none";
        timer = setInterval(() => {
            
        })
        generateVisualPlaylist();
    } else if (buttonType == "se") { //SearchMode button
        document.getElementById("songlist").innerHTML = "<h1>Search to find songs!</h1>";
        document.getElementById("playlist").innerHTML = "";
        document.getElementById("playlist-mode").style.display = "none";
        document.getElementById("songlist-mode").style.display = "block";
        document.getElementById("settings-mode").style.display = "none";
    } else if (buttonType == "st") { //Settings button
        document.getElementById("songlist").innerHTML = "";
        document.getElementById("playlist").innerHTML = "";
        document.getElementById("playlist-mode").style.display = "none";
        document.getElementById("songlist-mode").style.display = "none";
        document.getElementById("settings-mode").style.display = "block";
        checkSettings()
    } else if (buttonType = "pm") { //Partymode toggle (in settings)
        await getFromServer({setting: "partymode-toggle"}, "settings")
        checkSettings(true)
    }
    

}

function searchSongsEnter(e) {
    if (e.keyCode == 13) {
        searchSongs(document.getElementById("songsearch").value)
    }
}

async function searchSongs(searchTerm){
    document.getElementById("songlist").innerHTML = ""
    let fetchResults = await getFromServer({search:searchTerm},"search").then();
    let searchResults = fetchResults.data;
    //generate the visual song list
    for(var fileName in searchResults) {
        let currentSongInJSON = searchResults[fileName]
        let newItem = document.createElement("div");
        newItem.className = "item";
        newItem.id = fileName;
        newItem.tabIndex = 0;
        let image = document.createElement("img");
        try {
            if (currentSongInJSON["art"] == null) {
                throw "no image lolz"
            }
            image.src = currentSongInJSON["art"];
        } catch(err){
            image.src = "./images/placeholder.png";
        }
        image.id = String(fileName)+" image";
        let head3 = document.createElement("h3");
        head3.innerText = currentSongInJSON["title"];
        let head4 = document.createElement("h4");
        head4.innerText = currentSongInJSON["artist"];
        newItem.appendChild(image);
        newItem.appendChild(head3);
        newItem.appendChild(head4);
        // I like this concept but i'm leaving it out for now
        // if(currentSongInJSON.lossless === 1) {
        //     let losslesstag = document.createElement("p");
        //     losslesstag.textContent = "Ⓛ";
        //     losslesstag.classList.add("lossless-tag");
        //     newItem.appendChild(losslesstag);
        // }
        document.getElementById("songlist").appendChild(newItem);
    
    } 
    if (JSON.stringify(searchResults)==JSON.stringify({})) {
        //display error if no results
        document.getElementById("songlist").innerHTML = "<h1>We might not have that one...</h1>";
    }
}

function alertTimeEnter(e){
    if (e.key == "Enter") {
        e.preventDefault(); 
        alertTimeSet(document.getElementById("alerttimetextbox").value);
    }
}

function alertTimeSet(time) {
    alertTime = time;
    document.cookie = "alertTime="+alertTime+"; path=/;"
    alertText("Alerts stay on screen for " + alertTime.toString() + " seconds")
}

function ipSetEnter(e){
    if (e.key == "Enter") {
        e.preventDefault(); 
        ipSetter(document.getElementById("iptextbox").value)
    }
}

function ipSetter(){
    ipBox = document.getElementById("iptextbox").value
    if (ipBox == "") {
        alertText("Your IP is set to "+ip)
    } else {
        if (ipBox.includes(":")) {
            port = ipBox.slice(ipBox.indexOf(":")+1)
            ip = ipBox;
            document.cookie = "ip="+ip+"; path=/;"
            alertText("Your IP is now set to "+ip.slice(0, ipBox.indexOf(":"))+" at port "+port)
        } else {
            ip = ipBox + ":19054"
            document.cookie = "ip="+ip+"; path=/;"
            alertText("Your IP is now set to "+ipBox+" at port 19054 (Default)")
        }
    }
    // anytime the server ip changes the qrcode should change to use it
    qrCodeGenerate()
        
}

function qrCodeGenerate() {
    let tempURL = "http://" + document.location.href.split("/")[2] + "/?ip=" + ip;
    document.getElementById("qrcode").innerHTML = ""
    new QRCode(document.getElementById("qrcode"), {
        text: tempURL,
        width: 256,
        height: 256,
        colorDark : "#000000",
        colorLight : "#eeeeee",
        correctLevel : QRCode.CorrectLevel.H
    });
}

async function checkSettings(skipServer=false) {
    //check client stuff first so if the server doesn't exist it can still be changed and seen
    if (ip.slice(-5)=="19054") {
        // don't show the port if it is the default
        document.getElementById("iptextbox").value = ip.slice(0,-6)
    } else {
        document.getElementById("iptextbox").value = ip;
    }
    qrCodeGenerate()
    document.getElementById("alerttimetextbox").value = alertTime
    partyButtonState = document.getElementById("partymode-button").innerHTML;
    let nodeList = document.getElementById("admincheckholder").children
    // temporary
    for (let i=0; i<nodeList.length;i++) {
        if (nodeList[i].type == 'checkbox') {
            nodeList[i].checked = true;
        }
    }
    //ping the server here
    data = await getFromServer({setting: "getsettings"}, "settings");
    x = data["data"];
    if (!(skipServer) || partyButtonState=="N/A") {
        if (x["partymode"] == false) {
            document.getElementById("partymode-button").innerHTML = "Off";
        } else {
            document.getElementById("partymode-button").innerHTML = "On";
        }
    } else if (document.getElementById("partymode-button").innerHTML == "Off") {
        document.getElementById("partymode-button").innerHTML = "On";
    } else {
        document.getElementById("partymode-button").innerHTML = "Off";
    }
    document.getElementById("volumerange").value = parseInt(x["volume"])

    // do the admin checkboxes here
    let currentAdminPerms = x["admin"];
    document.getElementById("addsongsettingcheckbox").checked = currentAdminPerms["AS"];
    document.getElementById("skipsongsettingcheckbox").checked = currentAdminPerms["SK"];
    document.getElementById("playpausesettingcheckbox").checked = currentAdminPerms["PP"];
    document.getElementById("partymodesettingcheckbox").checked = currentAdminPerms["PM"];
    document.getElementById("volumechangesettingcheckbox").checked = currentAdminPerms["VOL"];
}

async function generateVisualPlaylist(conditions="") {
    document.getElementById("playlist").innerHTML = "<h1 id=\"playlist-alert\"></h1>";
    data = await getFromServer(null, "playlist");
    playlist = data["data"];
    playlist = Object.values(playlist).map(obj => {
        const filename = Object.keys(obj)[0]; // Get the filename
        const songData = obj[filename]; // Get the song metadata
        return { filename, ...songData }; // Merge filename with song data
      });
    if (playlist.length==0){
        document.getElementById("playlist-alert").innerHTML = "Nothing's Queued..."
    } else {
        if (conditions=="skip-button") {
            playlist.shift()
            if (playlist.length==0){
                document.getElementById("playlist-alert").innerHTML = "Nothing's Queued..."
            }
        }
        for (let i in playlist) {
            let fileName = playlist[i]["filename"]
            let newItem = document.createElement("div");
            newItem.className = "item";
            newItem.id = fileName;
            newItem.tabIndex = 0;
            let image = document.createElement("img");
            try {
                if (playlist[i]["art"] == null) {
                    throw "no image lolz"
                }
                image.src = playlist[i]["art"];
            } catch(err){
                image.src = "./images/placeholder.png";
            }
            image.id = String(fileName)+" image";
            let head3 = document.createElement("h3");
            head3.innerText = playlist[i]["title"];
            let head4 = document.createElement("h4");
            head4.innerText=playlist[i]["artist"];
            let head5 = document.createElement("h5");
            let timeLeft =document.createElement("h5");
            timeLeft.style.fontWeight = 100;
            try {
                if (i == 0) { // Only the first song in the loop gets a time
                    head5.innerHTML="Playing";
                    if ((conditions != "skip-button")) {
                        let mins = Math.floor(playlist[i]["time"]/60);
                        let secs = Math.floor(playlist[i]["time"]%60);
                        let durMins = Math.floor(playlist[i]["length"]/60);
                        let durSecs = Math.floor(playlist[i]["length"]%60);
                        timeLeft.innerHTML = mins.toString() +":"+ secs.toLocaleString('en-US', {minimumIntegerDigits: 2,useGrouping: false}) + "/"+ durMins.toString()+":"+durSecs.toLocaleString('en-US', {minimumIntegerDigits: 2,useGrouping: false});
                    }
                }
            }catch(err){
                // i dont know why there's a try catch here but i'm leaving it i dont want to break something
                console.error(err)
            }
            let textdiv = document.createElement("div")
            textdiv.className="text"
            newItem.appendChild(image);
            textdiv.appendChild(head3);
            textdiv.appendChild(head4);
            textdiv.appendChild(timeLeft);
            textdiv.appendChild(head5);
            newItem.appendChild(textdiv);
            document.getElementById("playlist").appendChild(newItem);
        }
    }  
}

async function submitSong(songid) {
    let returncode = await getFromServer({song: songid}, "songadd");
    if(returncode == ERR_NO_ADMIN) {
        // right now the error is alerted in getFromServer, maybe will change that
    } else if(returncode["error"]=="song-in-queue") {
        alertText("That song's about to play! Hang on!")
    } else {
        alertText("Added to Queue");
    }
}
function checkWhatSongWasClicked(e) {
    if(e.type == "click" || e.key == "Enter") {
        itemId = e.srcElement.id;
        if ((itemId.length-itemId.lastIndexOf("image") == 5) && itemId.lastIndexOf("image")!=-1) {
            itemId = itemId.slice(0,-6)
        }
        let filenameSep = itemId.split('.')
        //i feel like later kristy won't apreciate this
        //one of my files was "file.MP3" so it didn't work
        //windows be like
        if (VALID_FILE_EXT.includes(filenameSep[filenameSep.length-1].toLowerCase())) {
            submitSong(itemId);
        } 
    }
}

function toggleDark(e) {
    let x = document.getElementById("test-body").classList
    if (!(x.contains("dark-mode"))) {
        document.cookie = "darkmode=true; path=/;";
        document.getElementById("darkmode-button").innerHTML = "On";
        x.add("dark-mode");
    } else {
        document.cookie = "darkmode=false; path=/;";
        document.getElementById("darkmode-button").innerHTML = "Off";
        x.remove("dark-mode");
    }
    
}

async function sha256(message) {
    // Encode the message as UTF-8
    const msgBuffer = new TextEncoder().encode(message);

    // Hash the message
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);

    // Convert ArrayBuffer to hex string
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

    return hashHex;
}

async function adminPassEnter(e) {
    if (e.key == "Enter") {
        e.preventDefault();
        let enteredpass = document.getElementById("adminpasswordbox").value;
        if(enteredpass === "") {
            adminPass = ""; // an empty pass is technically meant to represent not having one
            // this isn't stritly necesarry but i dont wanna break anything that might depend on this being true
        } else {
            adminPass= await sha256(document.getElementById("adminpasswordbox").value);
        }
        alertText("Admin Password Updated");
    }
}

async function submitPerms(e) {
    let tempData = {}
    tempData["PP"] = document.getElementById("playpausesettingcheckbox").checked;
    tempData["SK"] = document.getElementById("skipsongsettingcheckbox").checked;
    tempData["AS"] = document.getElementById("addsongsettingcheckbox").checked;
    tempData["PM"] = document.getElementById("partymodesettingcheckbox").checked;
    tempData["VOL"] = document.getElementById("volumechangesettingcheckbox").checked;
    let returncode = await getFromServer({"setting":"perms","admin":tempData},"settings");
    if (returncode == ERR_NO_ADMIN || returncode == null) {
        // if you aren't allowed to check the box then toggle it again
        // its not perfect if you spam click, but it gets the point across to the user
        let clickedBox = e.srcElement;
        clickedBox.checked = !clickedBox.checked;
    }
}

async function clearPlaylist() {
    let returncode = await getFromServer({control:"clear"},"controls");
    if(returncode == ERR_NO_ADMIN || returncode == null) {
        // alertText("Admin Restricted ")
        // there's an admin restrict alert built into getFromServer
    } else {
        alertText("Playlist Cleared!");
    }
}

let optionslist = []

//sets all de stuff for buttons
document.addEventListener('keydown', function(e){
    if (e.key == "/"){
    document.getElementById("title").scrollIntoView();
    document.getElementById("songsearch").select();
    e.preventDefault()
}})
document.getElementById("playlist-mode").style.display = "none";
document.getElementById("settings-mode").style.display = "none";
document.getElementById("volumerange").onchange = async function() {
    // there is no reason for this not to be a defined function
    // FIX THIS
    let returnValue = await getFromServer({setting:"volume",level:this.value}, "settings")
    if (returnValue["status"] == ERR_NO_ADMIN) {
        // alertText("Error: Admin restricted action");
        // there's an admin restrict alert built into getFromServer
        // i wanna put the volume slider back to where it was but idk a good way to keep the previous volume
        checkSettings(false);
    } else if (returnValue["data"]["volumePassed"] !=0) {
        // i forgot about this, i had to do this because it confused the crap out of me one time
        // vlc doesn't let you change the volume of nothing, which makes sense if you think about it
        alertText("Nothing is playing")
        document.getElementById("volumerange").value = -1
    } else if (this.value == 0) {
        alertText("The volume is now set to 0 (Pause?)")
    } else {
        alertText("The volume is now set to " + this.value.toString())
    }
    
}


//bit of a cheat code for clearing the alerts when they don't clear normally
document.getElementById("title").addEventListener('click',function(){document.getElementById("alert").innerHTML = ""})
document.getElementById("settings-button").addEventListener('click',function(){controlButton("st")});
document.getElementById("play-pause-button").addEventListener('click', function(){controlButton("pp")});
document.getElementById("playlist-button").addEventListener('click', function(){controlButton("pl")});
document.getElementById("search-button").addEventListener('click', function(){controlButton("se")});
document.getElementById("skip-button").addEventListener('click',function(){controlButton("sk")});
document.getElementById("go-search").addEventListener('click', function(){searchSongs(document.getElementById("songsearch").value)})
document.getElementById("songsearch").addEventListener('keydown', function(e){searchSongsEnter(e)});
document.getElementById("iptextbox").addEventListener('keydown', function(e){ipSetEnter(e)});
document.getElementById("alerttimetextbox").addEventListener('keydown', function(e){alertTimeEnter(e)});
document.getElementById("adminpasswordbox").addEventListener('keydown',function(e){adminPassEnter(e)});
document.getElementById("admincheckholder").addEventListener('click',function(e){submitPerms(e)});
document.getElementById("partymode-button").addEventListener('click',function(){controlButton("pm")})
document.getElementById("darkmode-button").addEventListener('click',function(){toggleDark()})
document.getElementById("clear-button").addEventListener('click',function(){clearPlaylist()})
//sets the fact that clicking a song needs to return its id to the function to find it
document.getElementById("songlist").addEventListener('keydown', function(e){checkWhatSongWasClicked(e)});
document.getElementById("songlist").addEventListener('click', function(e){checkWhatSongWasClicked(e)});

//makes the controls look mostly normal on all screens, best solution i could find, idk man
let tempWidth = document.getElementById('controls').clientWidth;
document.getElementById("controls").style.marginLeft = "-"+String(parseInt(tempWidth/2))+"px";

//for my use case (my immediate family), they dont know how to set an ip
//using this allows the creator of the link for, a qr code for example, to set the ip before distributing the code, and it would all work smoothly
//example (http://192.168.1.100:8000/?ip=192.168.1.100:19054 sets the ip to the same host at the default port)
//the port must be set manually using this method, but only has to be done once for the url that ends up being shared

//tries the url first, then the cookie, then the default
ip = params.get("ip")
if (ip == null || ip=="") {
    ip=getCookie("ip")
}
if (ip==null || ip==""){
    ip = ""
}

// saving the cookies (don't tell the EU)
document.cookie = "ip="+ip+"; path=/;"

alertTime = getCookie("alertTime")
document.getElementById("alerttimetextbox").value = alertTime
if (alertTime == "") {
    alertTime = 2;
    document.cookie = "alertTime="+alertTime+"; path=/;"
}
// this is the code that makes the qr code at the very start
qrCodeGenerate()