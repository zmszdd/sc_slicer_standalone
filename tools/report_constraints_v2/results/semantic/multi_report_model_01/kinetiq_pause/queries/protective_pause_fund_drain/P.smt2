; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun confirm_call () Bool)
(declare-fun withdrawal_paused () Bool)
(declare-fun hype_withdrawn () Bool)
(declare-fun queued_withdrawal_ready () Bool)
(declare-fun withdrawal_pause_protective () Bool)
(assert
 (= confirm_call confirm_call))
(assert
 (= withdrawal_paused withdrawal_paused))
(assert
 (= hype_withdrawn hype_withdrawn))
(assert
 (= queued_withdrawal_ready queued_withdrawal_ready))
(assert
 (= withdrawal_pause_protective withdrawal_pause_protective))
(define-fun report_preconditions () Bool (and confirm_call queued_withdrawal_ready withdrawal_paused))
(define-fun report_safety () Bool (=> (and confirm_call withdrawal_paused) (not hype_withdrawn)))
(define-fun report_effects () Bool (and confirm_call withdrawal_paused withdrawal_pause_protective hype_withdrawn))
(assert report_preconditions)
(check-sat)
(get-model)
