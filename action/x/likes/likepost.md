# Liking X Post
This is a continuation automation from @action\x\findpost.py. So, when a task is received likepost, 

# Initial
- Run @action\x\findpost.py to find the post
- Wait for 5 seconds

# Automation
Then create automation in @action\x\likepost.py that do these:

1. Find this element:

<button aria-label="5004 Likes. Like" role="button" class="css-175oi2r r-1777fci r-bt1l66 r-bztko3 r-lrvibr r-1loqt21 r-1ny4l3l" data-testid="like" type="button"><div dir="ltr" class="css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-1awozwy r-6koalj r-1h0z5md r-o7ynqc r-clp7b1 r-3s2u2q" style="color: rgb(113, 118, 123);"><div class="css-175oi2r r-xoduu5"><div class="css-175oi2r r-xoduu5 r-1p0dtai r-1d2f490 r-u8s1d r-zchlnj r-ipm5af r-1niwhzg r-sdzlij r-xf4iuw r-o7ynqc r-6416eg r-1ny4l3l"></div><svg viewBox="0 0 24 24" aria-hidden="true" class="r-4qtqp9 r-yyyyoo r-dnmrzs r-bnwqim r-lrvibr r-m6rgpd r-1xvli5t r-1hdv0qi"><g><path d="M16.697 5.5c-1.222-.06-2.679.51-3.89 2.16l-.805 1.09-.806-1.09C9.984 6.01 8.526 5.44 7.304 5.5c-1.243.07-2.349.78-2.91 1.91-.552 1.12-.633 2.78.479 4.82 1.074 1.97 3.257 4.27 7.129 6.61 3.87-2.34 6.052-4.64 7.126-6.61 1.111-2.04 1.03-3.7.477-4.82-.561-1.13-1.666-1.84-2.908-1.91zm4.187 7.69c-1.351 2.48-4.001 5.12-8.379 7.67l-.503.3-.504-.3c-4.379-2.55-7.029-5.19-8.382-7.67-1.36-2.5-1.41-4.86-.514-6.67.887-1.79 2.647-2.91 4.601-3.01 1.651-.09 3.368.56 4.798 2.01 1.429-1.45 3.146-2.1 4.796-2.01 1.954.1 3.714 1.22 4.601 3.01.896 1.81.846 4.17-.514 6.67z"></path></g></svg></div><div class="css-175oi2r r-xoduu5 r-1udh08x"><span data-testid="app-text-transition-container" style="transition-property: transform; transition-duration: 0.3s; transform: translate3d(0px, 0px, 0px);"><span class="css-1jxf684 r-1ttztb7 r-qvutc0 r-poiln3 r-n6v787 r-1cwl3u0 r-1k6nrdp r-n7gxbd"><span class="css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3">5K</span></span></span></div></div></button>

inside

<article aria-labelledby="id\_\_n9dr87zahj id\_\_5j4v2gmnrgn id\_\_jxifc6ubqmd id\_\_hvzaosuvee id\_\_p2suimsw4ve id\_\_xewb6w1ya4c id\_\_si6f99u4sz id\_\_0xqu74f5mm1 id\_\_pia9sokr51q id\_\_wmcgury1kpg id\_\_4za6a3h9dme id\_\_fdvuutk2cir id\_\_ahsfc0ex2um id\_\_9e7gknu2tfo id\_\_nko4eniu7v id\_\_ig84zxiijcr id\_\_6lxewqayccv id\_\_s3gd91gmn8t id\_\_soyfa70o2cd id\_\_t4autzu02rq" role="article" tabindex="0" class="css-175oi2r r-18u37iz r-1udh08x r-1c4vpko r-1c7gwzm r-o7ynqc r-6416eg r-1ny4l3l r-1loqt21" data-testid="tweet"></article>


2. As usual, get its coordinates, send it to pyautogui move the mouse to the element using @action\mouse\initial\initial.py movement style, then click the element

3. Take screenshot immediately after clicking and save it to @action\x\screenshot

4. Create xhome_button.py in @action\x\home_button.py, to add this element inside

<a href="/home" aria-label="Home" role="link" class="css-175oi2r r-6koalj r-eqz5dr r-16y2uox r-1habvwh r-13qz1uu r-1mkv55d r-1ny4l3l r-1loqt21" data-testid="AppTabBar\_Home\_Link"><div class="css-175oi2r r-sdzlij r-dnmrzs r-1awozwy r-18u37iz r-1777fci r-xyw6el r-o7ynqc r-6416eg"><div class="css-175oi2r"><svg viewBox="0 0 24 24" aria-hidden="true" class="r-4qtqp9 r-yyyyoo r-dnmrzs r-bnwqim r-lrvibr r-m6rgpd r-1nao33i r-lwhw9o r-cnnz9e"><g><path d="M21.591 7.146L12.52 1.157c-.316-.21-.724-.21-1.04 0l-9.071 5.99c-.26.173-.409.456-.409.757v13.183c0 .502.418.913.929.913h6.638c.511 0 .929-.41.929-.913v-7.075h3.008v7.075c0 .502.418.913.929.913h6.639c.51 0 .928-.41.928-.913V7.904c0-.301-.158-.584-.408-.758zM20 20l-4.5.01.011-7.097c0-.502-.418-.913-.928-.913H9.44c-.511 0-.929.41-.929.913L8.5 20H4V8.773l8.011-5.342L20 8.764z"></path></g></svg></div><div dir="ltr" class="css-146c3p1 r-dnmrzs r-1udh08x r-1udbk01 r-3s2u2q r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-adyw6z r-135wba7 r-16dba41 r-dlybji r-nazi8o" style="color: rgb(231, 233, 234);"><span class="css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3">Home</span><span class="css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3"> </span></div></div></a>

5. Import @action\x\home_button.py in the automation process, then click that home button to get back to home

6. Switch to other tab (empty) in browser using @action\tab_switcher.py