"""User-specified demo experience; not inferred from rank or qualification."""
PROFILES={
 'FC1 Ochoa':{'level':'Experienced','repetitions':'>10 per maintenance item','guidance':'Concise reminders and relevant exceptions. Focus on recorded lessons and unusual conditions; offer detail on request.'},
 'FC2 Donohue':{'level':'Intermediate','repetitions':'3–4 per maintenance item','guidance':'Focused checkpoints, brief explanations of purpose, and relevant recorded pitfalls. Offer elaboration when requested.'},
 'FC3 Kluzak':{'level':'First time','repetitions':'0 prior completions; first attempt','guidance':'Detailed plain-language explanation of the current source step, terminology and prerequisites. Ask whether clarification is needed before progressing; do not invent missing instructions.'}
}
def for_sailor(name):
    return {'sailor':name or 'Unassigned','demo_profile':True,'basis':'User-specified demo experience across maintenance items; not verified history or qualification',**PROFILES.get(name,{'level':'Not specified','repetitions':'Unknown','guidance':'Use standard explanations and ask the technician how much detail they need.'})}

def greeting(name,job_title,resuming=False):
    opening='Welcome back' if resuming else 'Welcome aboard'
    experience={
        'FC1 Ochoa':"Your demo profile shows you've completed this maintenance more than 10 times. I'll keep guidance concise, focus on relevant lessons and exceptions, and provide more detail whenever you ask.",
        'FC2 Donohue':"Your demo profile shows you've completed this maintenance 3–4 times. I'll focus on key checkpoints and relevant lessons, with brief explanations where helpful.",
        'FC3 Kluzak':"Your demo profile shows this is your first time performing this maintenance. I'll explain the source material in plain language, help with terminology, and offer guidance as you work through it. Ask me to explain anything that is unclear."
    }.get(name,"I don't have an experience profile for this assignment yet. Select a sailor so I can tailor my guidance, or tell me how much explanation would help.")
    return f"{opening}, {name or 'sailor'}. Let's {'continue' if resuming else 'start'} {job_title}.\n\n{experience}\n\nRequired warnings and verification remain in place for every experience level."
