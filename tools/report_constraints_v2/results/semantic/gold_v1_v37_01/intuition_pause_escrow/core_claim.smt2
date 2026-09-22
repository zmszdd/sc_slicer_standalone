; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun is_paused () Bool)
(declare-fun has_escrow_entries () Bool)
(declare-fun escrow_transition_occurs () Bool)
(assert
 (= is_paused is_paused))
(assert
 (= has_escrow_entries has_escrow_entries))
(assert
 (= escrow_transition_occurs escrow_transition_occurs))
(define-fun report_preconditions () Bool (and is_paused has_escrow_entries))
(define-fun report_safety () Bool (=> is_paused (not escrow_transition_occurs)))
(define-fun report_effects () Bool (and is_paused escrow_transition_occurs))
