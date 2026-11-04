# -*- coding: utf-8 -*-
"""
CreatorBoost Bot - Internationalization (i18n) Module
Provides complete English and Hindi translations for all user-facing interactions.
"""

from typing import Dict, Any

STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        # General / Common
        "btn_back": "⬅️ Back to Menu",
        "btn_cancel": "❌ Cancel",
        "btn_confirm": "✅ Confirm & Claim",
        "btn_claim": "🎁 Claim Bonus",
        "btn_verify": "🔍 Verify Now",
        "btn_start_task": "▶️ Start Watching",
        "btn_proof": "📸 Submit Screenshot Proof",
        "btn_skip": "⏭️ Skip Campaign",
        "action_cancelled": "Action cancelled.",
        
        # Start & Welcome
        "welcome_msg": (
            "👋 <b>Welcome to CreatorBoost, {name}!</b>\n\n"
            "🚀 <i>The ultimate creator-exchange platform!</i>\n"
            "Earn coins by engaging with fellow YouTube creators, and spend coins "
            "to skyrocket your own video views, likes, and subscribers!\n\n"
            "💰 <b>Starter Bonus:</b> +{bonus} coins credited to your wallet!\n\n"
            "👇 Choose an option from the menu below to get started:"
        ),
        "choose_lang": "🌐 <b>Select Your Preferred Language / अपनी भाषा चुनें:</b>",
        "lang_updated": "✅ Language updated to English!",

        # Main Menu Buttons
        "menu_channel": "📺 My Channel",
        "menu_earn": "💰 Earn Coins",
        "menu_promote": "🚀 Promote Video",
        "menu_wallet": "👛 My Wallet",
        "menu_referral": "👥 Referral",
        "menu_daily": "🎁 Daily Bonus",
        "menu_buy_coins": "💎 Buy Coins",
        "menu_watch_ad": "📺 Watch Ad (+{coins})",
        "menu_help": "❓ Help & Rules",

        # Channel Verification Flow
        "channel_unverified_title": "📺 <b>Channel Registration</b>\n\n",
        "channel_prompt_link": (
            "To participate and earn coins, you must link your YouTube Channel!\n\n"
            "👉 Please send your <b>YouTube Channel Link</b> or <b>@handle</b>:\n"
            "<i>(Example: <code>https://youtube.com/@MrBeast</code> or <code>https://youtube.com/channel/UC...</code>)</i>"
        ),
        "channel_resolving": "⏳ Resolving channel details from YouTube API...",
        "channel_not_found": "❌ Channel could not be found. Please double-check your link or handle and try again.",
        "channel_already_registered": "⚠️ This YouTube channel is already registered by another Telegram account! Each channel can only be linked once.",
        "channel_verify_instructions": (
            "📺 <b>Channel Found:</b> <code>{title}</code>\n"
            "🆔 <b>Channel ID:</b> <code>{channel_id}</code>\n"
            "👥 <b>Subscribers:</b> {subscribers:,}\n\n"
            "🔐 <b>Ownership Verification Step:</b>\n"
            "1. Copy this unique verification code: <code>{code}</code>\n"
            "2. Paste it anywhere in your YouTube channel's <b>About / Description</b>.\n"
            "3. Click the <b>[🔍 Verify Now]</b> button below.\n\n"
            "<i>(You can remove the code right after verification completes!)</i>"
        ),
        "channel_verify_success": (
            "🎉 <b>Channel Verified Successfully!</b>\n\n"
            "Your channel <b>{title}</b> is now officially linked to your account.\n"
            "You are fully eligible to earn coins and launch promotion campaigns!"
        ),
        "channel_verify_fail": (
            "❌ <b>Verification Failed!</b>\n\n"
            "We could not find the code <code>{code}</code> in your channel's About section.\n"
            "Please ensure you saved your channel description on YouTube and try again."
        ),
        "channel_info_verified": (
            "📺 <b>Linked YouTube Channel</b>\n\n"
            "• <b>Name:</b> {title}\n"
            "• <b>Handle:</b> {custom_url}\n"
            "• <b>Channel ID:</b> <code>{channel_id}</code>\n"
            "• <b>Subscribers:</b> {subscribers:,}\n"
            "• <b>Status:</b> ✅ Verified\n"
            "• <b>Verified On:</b> {verified_at}"
        ),

        # Earn Coins Flow
        "earn_no_campaigns": (
            "📭 <b>No Active Campaigns Right Now!</b>\n\n"
            "There are currently no campaigns available for you.\n"
            "Please check back in a few minutes, or promote your own video!"
        ),
        "earn_campaign_card": (
            "🎬 <b>Available Task: {task_type}</b>\n\n"
            "📌 <b>Video:</b> <a href=\"{video_url}\">{video_title}</a>\n"
            "💰 <b>Reward:</b> +{reward} Coins\n"
            "⏱ <b>Requirement:</b> {instruction}\n\n"
            "👇 Click the link to open the video, complete the task, then confirm below:"
        ),
        "task_instr_watch": "Watch the video for at least {seconds} seconds. Timer will run below.",
        "task_instr_like": "Like the video and submit screenshot proof.",
        "task_instr_comment": "Leave a genuine comment and submit screenshot proof.",
        "task_instr_sub": "Subscribe to the channel. (Your subscription list must be public).",
        "task_timer_running": "⏳ <b>Watching in progress...</b> Please keep watching for {remaining} seconds before confirming.",
        "task_confirmed_reward": "🎉 <b>Task Completed!</b> +{reward} coins have been credited to your wallet!",
        "task_proof_submitted": "📸 <b>Proof Submitted!</b> An admin will review your screenshot shortly. Coins will be credited upon approval.",
        "task_cooldown_active": "⏳ Please wait {seconds}s before starting another task.",
        "task_already_attempted": "⚠️ You have already completed or attempted this task.",

        # Promote Video Flow
        "promote_intro": (
            "🚀 <b>Promote Your YouTube Video</b>\n\n"
            "Select the type of engagement you want for your video:"
        ),
        "promote_ask_url": "🔗 Please send the <b>YouTube Video Link</b> you want to promote:",
        "promote_invalid_url": "❌ Invalid YouTube URL. Please send a valid link (e.g. <code>https://youtu.be/...</code>)",
        "promote_ask_quantity": (
            "🎬 <b>Video:</b> <code>{title}</code>\n"
            "📌 <b>Task:</b> {task_type}\n"
            "💰 <b>Cost per Action:</b> {cost} coins\n\n"
            "👉 How many actions do you want? (Min: 5, Max: 500):"
        ),
        "promote_insufficient_coins": (
            "❌ <b>Insufficient Coins!</b>\n\n"
            "Total Cost: <b>{total_cost} coins</b>\n"
            "Your Balance: <b>{balance} coins</b>\n\n"
            "Earn coins by engaging with others or purchase a coin pack!"
        ),
        "promote_success": (
            "🎉 <b>Campaign Launched!</b>\n\n"
            "• <b>Video:</b> {title}\n"
            "• <b>Type:</b> {task_type}\n"
            "• <b>Goal:</b> {quantity} actions\n"
            "• <b>Total Spent:</b> {total_cost} coins\n\n"
            "Your campaign is now live for all creators to view!"
        ),

        # Wallet
        "wallet_card": (
            "👛 <b>Your Creator Wallet</b>\n\n"
            "💰 <b>Balance:</b> <code>{coins}</code> Coins\n"
            "📊 <b>Tasks Completed:</b> {completed_tasks}\n"
            "👥 <b>Active Campaigns:</b> {active_campaigns}\n\n"
            "📜 <b>Recent Transactions:</b>\n{tx_history}"
        ),

        # Referral
        "referral_card": (
            "👥 <b>Creator Referral Program</b>\n\n"
            "Invite other YouTubers and earn <b>+{reward} Coins</b> for every creator who:\n"
            "1. Joins using your referral link.\n"
            "2. Links & verifies their YouTube channel.\n"
            "3. Completes their first {threshold} tasks.\n\n"
            "🔗 <b>Your Exclusive Referral Link:</b>\n"
            "<code>{ref_link}</code>\n\n"
            "📊 <b>Your Referral Stats:</b>\n"
            "• Total Invited: <b>{total_referred}</b>\n"
            "• Qualified Creators: <b>{qualified}</b>\n"
            "• Coins Earned: <b>+{total_coins}</b>"
        ),

        # Daily Bonus
        "daily_bonus_claimed": (
            "🎁 <b>Daily Bonus Claimed!</b>\n\n"
            "• Streak Day: <b>Day {streak} / 7</b> 🔥\n"
            "• Reward: <b>+{coins} Coins</b>\n\n"
            "Come back tomorrow to keep your streak alive and unlock higher rewards!"
        ),
        "daily_bonus_cooldown": (
            "⏳ <b>Already Claimed Today!</b>\n\n"
            "Next bonus available in: <b>{time_left}</b>\n"
            "Current Streak: Day {streak} 🔥"
        ),

        # Buy Coins
        "buy_coins_intro": (
            "💎 <b>CreatorBoost Coin Shop</b>\n\n"
            "Accelerate your channel growth with premium coin packs.\n"
            "Pay seamlessly with <b>Telegram Stars</b> or direct <b>UPI</b>:"
        ),

        # Help
        "help_text": (
            "❓ <b>CreatorBoost Bot Help & Guidelines</b>\n\n"
            "1. <b>Earn Coins:</b> Watch, like, and comment on other creators' videos.\n"
            "2. <b>Promote:</b> Use earned coins to run campaigns for your own channel.\n"
            "3. <b>Fair Play Rules:</b>\n"
            "• Do not immediately unlike or unsubscribe, or your account will be flagged.\n"
            "• Always let the watch timer finish.\n"
            "• Multiple accounts or automated bots will result in permanent ban."
        )
    },
    "hi": {
        # General / Common
        "btn_back": "⬅️ मुख्य मेनू",
        "btn_cancel": "❌ रद्द करें",
        "btn_confirm": "✅ पुष्टि करें और सिक्के लें",
        "btn_claim": "🎁 बोनस क्लेम करें",
        "btn_verify": "🔍 अभी सत्यापित करें",
        "btn_start_task": "▶️ देखना शुरू करें",
        "btn_proof": "📸 स्क्रीनशॉट प्रमाण भेजें",
        "btn_skip": "⏭️ अगला कार्य",
        "action_cancelled": "प्रक्रिया रद्द कर दी गई।",
        
        # Start & Welcome
        "welcome_msg": (
            "👋 <b>CreatorBoost में आपका स्वागत है, {name}!</b>\n\n"
            "🚀 <i>क्रिएटर्स का सबसे भरोसेमंद एक्सचेंज प्लेटफॉर्म!</i>\n"
            "अन्य YouTube क्रिएटर्स के वीडियो देखकर सिक्के (Coins) कमाएं और अपने खुद के "
            "वीडियो के व्यूज, लाइक्स और सब्सक्राइबर्स तेजी से बढ़ाएं!\n\n"
            "💰 <b>शुरुआती बोनस:</b> +{bonus} सिक्के आपके वॉलेट में जोड़ दिए गए हैं!\n\n"
            "👇 शुरू करने के लिए नीचे दिए गए मेनू में से विकल्प चुनें:"
        ),
        "choose_lang": "🌐 <b>अपनी पसंदीदा भाषा चुनें / Select Your Preferred Language:</b>",
        "lang_updated": "✅ भाषा बदलकर हिंदी कर दी गई है!",

        # Main Menu Buttons
        "menu_channel": "📺 मेरा चैनल",
        "menu_earn": "💰 सिक्के कमाएं",
        "menu_promote": "🚀 वीडियो प्रमोट करें",
        "menu_wallet": "👛 मेरा वॉलेट",
        "menu_referral": "👥 रेफरल",
        "menu_daily": "🎁 दैनिक बोनस",
        "menu_buy_coins": "💎 सिक्के खरीदें",
        "menu_watch_ad": "📺 विज्ञापन देखें (+{coins})",
        "menu_help": "❓ सहायता एवं नियम",

        # Channel Verification Flow
        "channel_unverified_title": "📺 <b>चैनल पंजीकरण</b>\n\n",
        "channel_prompt_link": (
            "सिक्के कमाने और वीडियो प्रमोट करने के लिए अपना YouTube चैनल लिंक करना अनिवार्य है!\n\n"
            "👉 कृपया अपने <b>YouTube चैनल का लिंक</b> या <b>@handle</b> भेजें:\n"
            "<i>(उदाहरण: <code>https://youtube.com/@handle</code> या <code>https://youtube.com/channel/UC...</code>)</i>"
        ),
        "channel_resolving": "⏳ YouTube API से चैनल की जानकारी जांची जा रही है...",
        "channel_not_found": "❌ चैनल नहीं मिला। कृपया अपने लिंक की जांच करें और पुनः प्रयास करें।",
        "channel_already_registered": "⚠️ यह YouTube चैनल पहले से ही किसी अन्य टेलीग्राम खाते द्वारा लिंक किया गया है!",
        "channel_verify_instructions": (
            "📺 <b>चैनल मिल गया:</b> <code>{title}</code>\n"
            "🆔 <b>चैनल आईडी:</b> <code>{channel_id}</code>\n"
            "👥 <b>सब्सक्राइबर्स:</b> {subscribers:,}\n\n"
            "🔐 <b>स्वामित्व सत्यापन चरण:</b>\n"
            "1. यह गुप्त कोड कॉपी करें: <code>{code}</code>\n"
            "2. इसे अपने YouTube चैनल के <b>About / विवरण (Description)</b> में पेस्ट करें।\n"
            "3. नीचे दिए गए <b>[🔍 अभी सत्यापित करें]</b> बटन पर क्लिक करें।\n\n"
            "<i>(सत्यापन पूरा होने के तुरंत बाद आप इस कोड को हटा सकते हैं!)</i>"
        ),
        "channel_verify_success": (
            "🎉 <b>चैनल सफलतापूर्वक सत्यापित हो गया!</b>\n\n"
            "आपका चैनल <b>{title}</b> अब सफलतापूर्वक लिंक हो चुका है।\n"
            "अब आप सिक्के कमा सकते हैं और अपने वीडियो का प्रमोशन शुरू कर सकते हैं!"
        ),
        "channel_verify_fail": (
            "❌ <b>सत्यापन विफल रहा!</b>\n\n"
            "हमें आपके चैनल के About सेक्शन में कोड <code>{code}</code> नहीं मिला।\n"
            "कृपया सुनिश्चित करें कि आपने YouTube पर विवरण सहेज लिया है और पुनः प्रयास करें।"
        ),
        "channel_info_verified": (
            "📺 <b>लिंक किया गया YouTube चैनल</b>\n\n"
            "• <b>नाम:</b> {title}\n"
            "• <b>हैंडल:</b> {custom_url}\n"
            "• <b>चैनल आईडी:</b> <code>{channel_id}</code>\n"
            "• <b>सब्सक्राइबर्स:</b> {subscribers:,}\n"
            "• <b>स्थिति:</b> ✅ सत्यापित (Verified)\n"
            "• <b>सत्यापित तिथि:</b> {verified_at}"
        ),

        # Earn Coins Flow
        "earn_no_campaigns": (
            "📭 <b>वर्तमान में कोई नया कार्य उपलब्ध नहीं है!</b>\n\n"
            "अभी आपके लिए कोई एक्टिव कैंपेन नहीं है।\n"
            "कृपया थोड़ी देर बाद पुनः देखें, या अपना खुद का वीडियो प्रमोट करें!"
        ),
        "earn_campaign_card": (
            "🎬 <b>उपलब्ध कार्य: {task_type}</b>\n\n"
            "📌 <b>वीडियो:</b> <a href=\"{video_url}\">{video_title}</a>\n"
            "💰 <b>इनाम:</b> +{reward} सिक्के\n"
            "⏱ <b>नियम:</b> {instruction}\n\n"
            "👇 लिंक पर क्लिक करके कार्य पूरा करें और नीचे पुष्टि करें:"
        ),
        "task_instr_watch": "वीडियो को कम से कम {seconds} सेकंड देखें। टाइमर नीचे चलेगा।",
        "task_instr_like": "वीडियो लाइक करें और स्क्रीनशॉट प्रूफ भेजें।",
        "task_instr_comment": "सकारात्मक कमेंट करें और स्क्रीनशॉट प्रूफ भेजें।",
        "task_instr_sub": "चैनल को सब्सक्राइब करें। (आपकी सब्सक्रिप्शन लिस्ट पब्लिक होनी चाहिए)।",
        "task_timer_running": "⏳ <b>वीडियो देखना जारी है...</b> कृपया पुष्टि करने से पहले {remaining} सेकंड प्रतीक्षा करें।",
        "task_confirmed_reward": "🎉 <b>कार्य पूरा हुआ!</b> +{reward} सिक्के आपके वॉलेट में जोड़ दिए गए हैं!",
        "task_proof_submitted": "📸 <b>प्रमाण प्राप्त हुआ!</b> एडमिन जल्द ही स्क्रीनशॉट की जांच करेंगे। स्वीकृति के बाद सिक्के जमा होंगे।",
        "task_cooldown_active": "⏳ कृपया अगला कार्य शुरू करने से पहले {seconds} सेकंड प्रतीक्षा करें।",
        "task_already_attempted": "⚠️ आप इस कार्य को पहले ही पूरा या प्रयास कर चुके हैं।",

        # Promote Video Flow
        "promote_intro": (
            "🚀 <b>अपना YouTube वीडियो प्रमोट करें</b>\n\n"
            "चुनें कि आप अपने वीडियो पर किस प्रकार का एंगेजमेंट चाहते हैं:"
        ),
        "promote_ask_url": "🔗 कृपया वह <b>YouTube वीडियो लिंक</b> भेजें जिसे आप प्रमोट करना चाहते हैं:",
        "promote_invalid_url": "❌ अमान्य YouTube लिंक। कृपया सही लिंक भेजें (उदा. <code>https://youtu.be/...</code>)",
        "promote_ask_quantity": (
            "🎬 <b>वीडियो:</b> <code>{title}</code>\n"
            "📌 <b>कार्य प्रकार:</b> {task_type}\n"
            "💰 <b>प्रति कार्य लागत:</b> {cost} सिक्के\n\n"
            "👉 आपको कितने एक्शन्स चाहिए? (न्यूनतम: 5, अधिकतम: 500):"
        ),
        "promote_insufficient_coins": (
            "❌ <b>सिक्के अपर्याप्त हैं!</b>\n\n"
            "कुल लागत: <b>{total_cost} सिक्के</b>\n"
            "आपका बैलेंस: <b>{balance} सिक्के</b>\n\n"
            "अन्य क्रिएटर्स के वीडियो देखकर सिक्के कमाएं या कॉइन पैक खरीदें!"
        ),
        "promote_success": (
            "🎉 <b>कैंपेन सफलतापूर्वक शुरू हुआ!</b>\n\n"
            "• <b>वीडियो:</b> {title}\n"
            "• <b>प्रकार:</b> {task_type}\n"
            "• <b>लक्ष्य:</b> {quantity} एक्शन्स\n"
            "• <b>कुल खर्च:</b> {total_cost} सिक्के\n\n"
            "आपका कैंपेन अब सभी क्रिएटर्स को दिखाई देगा!"
        ),

        # Wallet
        "wallet_card": (
            "👛 <b>आपका क्रिएटर वॉलेट</b>\n\n"
            "💰 <b>कुल बैलेंस:</b> <code>{coins}</code> सिक्के\n"
            "📊 <b>पूरे किए गए कार्य:</b> {completed_tasks}\n"
            "👥 <b>सक्रिय कैंपेन:</b> {active_campaigns}\n\n"
            "📜 <b>हाल के लेन-देन:</b>\n{tx_history}"
        ),

        # Referral
        "referral_card": (
            "👥 <b>क्रिएटर रेफरल प्रोग्राम</b>\n\n"
            "अन्य YouTubers को आमंत्रित करें और प्रत्येक क्रिएटर पर <b>+{reward} सिक्के</b> कमाएं जो:\n"
            "1. आपके लिंक से जुड़े।\n"
            "2. अपना YouTube चैनल सत्यापित करे।\n"
            "3. अपने पहले {threshold} कार्य पूरे करे।\n\n"
            "🔗 <b>आपका विशेष रेफरल लिंक:</b>\n"
            "<code>{ref_link}</code>\n\n"
            "📊 <b>रेफरल आंकड़े:</b>\n"
            "• कुल आमंत्रित: <b>{total_referred}</b>\n"
            "• योग्य क्रिएटर्स: <b>{qualified}</b>\n"
            "• कुल कमाई: <b>+{total_coins} सिक्के</b>"
        ),

        # Daily Bonus
        "daily_bonus_claimed": (
            "🎁 <b>दैनिक बोनस प्राप्त हुआ!</b>\n\n"
            "• स्ट्रीक दिन: <b>दिन {streak} / 7</b> 🔥\n"
            "• इनाम: <b>+{coins} सिक्के</b>\n\n"
            "अपनी स्ट्रीक जारी रखने और बड़ा इनाम पाने के लिए कल फिर आएं!"
        ),
        "daily_bonus_cooldown": (
            "⏳ <b>आज का बोनस पहले ही क्लेम किया जा चुका है!</b>\n\n"
            "अगला बोनस उपलब्ध होगा: <b>{time_left}</b> में\n"
            "वर्तमान स्ट्रीक: दिन {streak} 🔥"
        ),

        # Buy Coins
        "buy_coins_intro": (
            "💎 <b>CreatorBoost कॉइन स्टोर</b>\n\n"
            "प्रीमियम कॉइन पैक के साथ अपने चैनल की वृद्धि को गति दें।\n"
            "<b>Telegram Stars</b> या सीधे <b>UPI</b> से तुरंत भुगतान करें:"
        ),

        # Help
        "help_text": (
            "❓ <b>CreatorBoost बॉट सहायता एवं दिशानिर्देश</b>\n\n"
            "1. <b>सिक्के कमाएं:</b> अन्य क्रिएटर्स के वीडियो देखें, लाइक करें और कमेंट करें।\n"
            "2. <b>प्रमोट करें:</b> कमाए गए सिक्कों से अपने खुद के वीडियो प्रमोट करें।\n"
            "3. <b>नियम:</b>\n"
            "• कार्य करने के बाद अनसब्सक्राइब या अनलाइक न करें, अन्यथा खाता ब्लॉक कर दिया जाएगा।\n"
            "• टाइमर पूरा होने से पहले बॉट बंद न करें।"
        )
    }
}

def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    """Retrieve translated string with formatted keyword arguments."""
    lang_dict = STRINGS.get(lang, STRINGS["en"])
    template = lang_dict.get(key, STRINGS["en"].get(key, f"[{key}]"))
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
