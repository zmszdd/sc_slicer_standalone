; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb08e9884_deadline_specifiable () Bool)
(declare-fun cb08e9884_executed_at_unexpected_time () Bool)
(declare-fun cb08e9884_slippage_protection_present () Bool)
(declare-fun cb08e9884_swap_submitted () Bool)
(assert
 (= cb08e9884_deadline_specifiable cb08e9884_deadline_specifiable))
(assert
 (= cb08e9884_executed_at_unexpected_time cb08e9884_executed_at_unexpected_time))
(assert
 (= cb08e9884_slippage_protection_present cb08e9884_slippage_protection_present))
(assert
 (= cb08e9884_swap_submitted cb08e9884_swap_submitted))
(define-fun report_preconditions () Bool (and cb08e9884_swap_submitted
     (not cb08e9884_deadline_specifiable)
     cb08e9884_slippage_protection_present))
(define-fun report_safety () Bool (=> (and cb08e9884_swap_submitted
         (not cb08e9884_deadline_specifiable)
         cb08e9884_slippage_protection_present)
    (not cb08e9884_executed_at_unexpected_time)))
(define-fun report_effects () Bool (and cb08e9884_swap_submitted
     (not cb08e9884_deadline_specifiable)
     cb08e9884_slippage_protection_present
     (not (not cb08e9884_executed_at_unexpected_time))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
