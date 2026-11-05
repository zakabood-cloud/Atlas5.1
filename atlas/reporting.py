"""Human-readable footnote export. Does not certify source semantics or research accuracy."""
import re
from pathlib import Path
from .io import AtlasError, atomic_text
from .verification import MARKER,report_audit


def render_markdown(body,evidence,limited=False,limitations=''):
    if not body.strip():raise AtlasError('Cannot render an empty report')
    claims={c['id']:c for c in evidence.get('claims',[])}
    sources={s['id']:s for s in evidence.get('sources',[])}
    ordered=[]
    def cite(match):
        cid=match.group(1)
        if cid not in claims: return '[UNRESOLVED CLAIM '+cid+']'
        if cid not in ordered:ordered.append(cid)
        return f'[{ordered.index(cid)+1}]'
    text=MARKER.sub(cite,body)
    if limited:
        text='> **LIMITED / UNVERIFIED RESEARCH:** The research workflow is incomplete. The following output is NOT a verified ATLAS report. '+(limitations or 'Evidence or review requirements are missing.')+'\n\n'+text
    if ordered:
        text+='\n\n## References and evidence notes\n\n'
        for i,cid in enumerate(ordered,1):
            claim=claims[cid];refs=[]
            for sid in claim.get('source_ids',[]):
                s=sources.get(sid)
                if s:refs.append(f'{s.get("title",sid)} — {s.get("url","missing URL")}' + (' (provisional search snippet)' if s.get('source_type')=='search_result' else ''))
            text+=f'{i}. **{cid}:** {claim["text"]}  '+ ' | '.join(refs)+'\n'
    return text


def limited_report(project,report,reason,out_name='outputs/limited-report.md'):
    if not reason.strip():raise AtlasError('Limited report needs a clear, material evidence limitation')
    if Path(out_name).is_absolute() or '..' in Path(out_name).parts or not out_name.startswith('outputs/'):
        raise AtlasError('Limited report output must be within outputs/')
    from .io import confined,atomic_json,now
    path=confined(project.path,out_name)
    data=project.artifact('evidence.json')
    body=report.read_text(encoding='utf-8')
    rendered=render_markdown(body,data,limited=True,limitations=reason)
    atomic_text(path,rendered)
    receipt={'state':project.status()['state'],'path':out_name,'at':now(),'reason':reason,
             'status':'LIMITED_NOT_VERIFIED','claim_count':len(data['claims']),
             'audit':report_audit(body,data,strict=False)}
    atomic_json(project.path/'outputs/limited-report-receipt.json',receipt)
    return receipt


def export_report(project,input_file,output,fmt='md',limited=False,limitations=''):
    from .io import confined
    source=Path(input_file)
    if not source.is_absolute():source=confined(project.path,str(source),True)
    else:
        source=source.resolve()
        if not source.is_relative_to(project.path):raise AtlasError('Report input must belong to the project')
    target=Path(output)
    if target.is_absolute() or '..' in target.parts or not str(target).startswith('outputs/'):
        raise AtlasError('Output path must be project-relative under outputs/')
    result=render_markdown(source.read_text(encoding='utf-8'),project.artifact('evidence.json'),limited,limitations)
    dest=confined(project.path,str(target))
    if fmt=='md':
        atomic_text(dest,result)
    elif fmt=='pdf':
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Preformatted
            from reportlab.lib.styles import getSampleStyleSheet
            from xml.sax.saxutils import escape
        except ImportError as exc:raise AtlasError('PDF export needs optional ReportLab: pip install .[pdf]') from exc
        styles=getSampleStyleSheet();parts=[]
        for line in result.splitlines():
            if not line.strip():parts.append(Spacer(1,6));continue
            if line.startswith('# '):style=styles['Title'];line=line[2:]
            elif line.startswith('## '):style=styles['Heading2'];line=line[3:]
            elif line.startswith('### '):style=styles['Heading3'];line=line[4:]
            else:style=styles['BodyText']
            # Paragraph escapes all HTML from untrusted retrieval content.
            parts.append(Paragraph(escape(line),style))
        doc=SimpleDocTemplate(str(dest),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=52,bottomMargin=48)
        doc.build(parts)
    else:raise AtlasError('Supported render formats: md, pdf')
    return {'output':str(target),'format':fmt,'status':'rendered_not_semantically_verified','size_bytes':dest.stat().st_size}
