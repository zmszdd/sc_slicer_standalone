; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c83f635ff_slashing_event_pending () Bool)
(declare-fun c83f635ff_slashing_penalty_incurred () Bool)
(declare-fun c83f635ff_staked_amounts_large () Bool)
(declare-fun c83f635ff_withdrawal_queued_before_slashing () Bool)
(assert
 (= c83f635ff_slashing_event_pending c83f635ff_slashing_event_pending))
(assert
 (= c83f635ff_slashing_penalty_incurred c83f635ff_slashing_penalty_incurred))
(assert
 (= c83f635ff_staked_amounts_large c83f635ff_staked_amounts_large))
(assert
 (= c83f635ff_withdrawal_queued_before_slashing c83f635ff_withdrawal_queued_before_slashing))
(define-fun report_preconditions () Bool (and c83f635ff_slashing_event_pending c83f635ff_staked_amounts_large))
(define-fun report_safety () Bool (=> (and c83f635ff_slashing_event_pending c83f635ff_staked_amounts_large)
    (and c83f635ff_withdrawal_queued_before_slashing
         c83f635ff_slashing_penalty_incurred)))
(define-fun report_effects () Bool (and c83f635ff_slashing_event_pending
     c83f635ff_staked_amounts_large
     (not (and c83f635ff_withdrawal_queued_before_slashing
               c83f635ff_slashing_penalty_incurred))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
