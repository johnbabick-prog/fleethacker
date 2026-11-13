"""Keep local model reasoning/channel markup out of technician-facing responses."""
import re
NO_ANSWER='The local model did not return a final answer. Please retry; the recorded step reminders remain available.'
def final_answer(content):
    if not isinstance(content,str):return NO_ANSWER
    text=content
    # Gemma 4 closes its private thought block with <channel|>, then emits
    # the final answer. The block may be empty when thinking is disabled.
    # https://ai.google.dev/gemma/docs/core/prompt-formatting-gemma4
    thought = re.search(r'<\|channel>\s*thought\b', text, re.I)
    if thought:
        close = text.find('<channel|>', thought.end())
        if close >= 0:
            text = text[close + len('<channel|>'):]
    # Some compatible servers put channel markup inside content instead of separate fields.
    final=list(re.finditer(r'<\|channel\|?>\s*(?:final|answer)\b|<\|im_sep\|>\s*final\b',text,re.I))
    if final:text=text[final[-1].end():]
    elif re.search(r'<\|channel\|?>\s*(?:thought|analysis)\b',text,re.I):return NO_ANSWER
    text=re.sub(r'<(?:think|analysis|thought)>.*?</(?:think|analysis|thought)>','',text,flags=re.S|re.I)
    text=re.sub(r'<(?:think|analysis|thought)>.*$','',text,flags=re.S|re.I)
    text=re.sub(r'<\|[^>]*>|<turn\|>|<channel\|>','',text).strip()
    return text or NO_ANSWER

def record_fallback(context):
    """Useful evidence, explicitly not a generated answer to an unsupported question."""
    step=context.get('active_step')
    if not step:return 'Local AI could not produce an answer. Review the retrieved references below; no generated recommendation is available.'
    lines=['Local-record fallback — AI explanation unavailable.',f"Step {step['number']} of {step['total']}: {step['instruction']}"]
    corrections=context.get('sailor_recorded_corrections',[])
    lessons=context.get('lessons',[])
    seen=set()
    for record in (corrections+lessons):
        if record['id'] in seen:continue
        seen.add(record['id'])
        label='Recorded lesson' if record.get('kind')=='observation' else 'Recorded observation'
        lines.append(label+': '+record['text'])
        if len(seen)>=2:break
    if not seen:lines.append('No step-specific lessons are recorded. Follow the displayed task card; ask your supervisor about missing requirements.')
    return '\n\n'.join(lines)
