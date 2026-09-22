; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun fok_submitted () Bool)
(declare-fun only_dust_unfilled () Bool)
(declare-fun user_not_charged_dust () Bool)
(declare-fun reverted () Bool)
(assert
 (= fok_submitted fok_submitted))
(assert
 (= only_dust_unfilled only_dust_unfilled))
(assert
 (= user_not_charged_dust user_not_charged_dust))
(assert
 (= reverted reverted))
(define-fun report_preconditions () Bool (and fok_submitted only_dust_unfilled user_not_charged_dust))
(define-fun report_safety () Bool (=> (and only_dust_unfilled user_not_charged_dust) (not reverted)))
(define-fun report_effects () Bool (and only_dust_unfilled reverted))
