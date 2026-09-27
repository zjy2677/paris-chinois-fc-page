import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
type Mode = 'login' | 'forgot' | 'create';
export function LoginModal({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const [mode, setMode] = useState<Mode>('login');
  const [feedback, setFeedback] = useState('');
  const changeMode = (next: Mode) => { setMode(next); setFeedback(''); };
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent className="max-w-md border-border bg-card p-8 text-foreground shadow-2xl">
    <DialogHeader className="text-left"><p className="eyebrow text-copper">Members area</p><DialogTitle className="font-display text-5xl font-bold uppercase">{mode === 'login' ? 'Log in' : mode === 'forgot' ? 'Reset password' : 'Create account'}</DialogTitle><DialogDescription className="text-muted-foreground">Prototype access only. No account or email service is connected.</DialogDescription></DialogHeader>
    <form className="mt-5 space-y-4" onSubmit={e => { e.preventDefault(); setFeedback(mode === 'forgot' ? 'Demo only — no reset email was sent.' : mode === 'create' ? 'Demo only — no account was created.' : 'Demo only — sign in is not available yet.'); }}>
      <label className="block text-sm">Email address<input required type="email" autoComplete="email" className="mt-2 h-12 w-full border border-border bg-background px-3 text-foreground" placeholder="you@example.com" /></label>
      {mode !== 'forgot' && <label className="block text-sm">Password<input required minLength={8} type="password" autoComplete={mode === 'create' ? 'new-password' : 'current-password'} className="mt-2 h-12 w-full border border-border bg-background px-3 text-foreground" placeholder="At least 8 characters" /></label>}
      <Button type="submit" className="h-12 w-full rounded-none bg-primary font-bold uppercase tracking-wider text-primary-foreground hover:bg-primary/85">{mode === 'forgot' ? 'Send reset link' : mode === 'create' ? 'Create account' : 'Log in'}</Button>
      {feedback && <p role="status" className="border-l-2 border-copper pl-3 text-sm text-copper">{feedback}</p>}
    </form>
    <div className="flex justify-between gap-3 border-t border-border pt-5 text-sm"><Button variant="link" className="h-auto p-0 text-muted-foreground" onClick={() => changeMode(mode === 'forgot' ? 'login' : 'forgot')}>{mode === 'forgot' ? 'Back to log in' : 'Forgot password?'}</Button><Button variant="link" className="h-auto p-0 text-copper" onClick={() => changeMode(mode === 'create' ? 'login' : 'create')}>{mode === 'create' ? 'Log in instead' : 'Create account'}</Button></div>
  </DialogContent></Dialog>;
}
