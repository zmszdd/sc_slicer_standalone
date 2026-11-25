; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c335b67af_notified_emission_recoverable () Bool)
(declare-fun c335b67af_notified_emission_tracked () Bool)
(declare-fun c335b67af_notified_emission_untracked () Bool)
(declare-fun c335b67af_voter_total_weight () Int)
(assert
 (= c335b67af_notified_emission_recoverable c335b67af_notified_emission_recoverable))
(assert
 (= c335b67af_notified_emission_tracked c335b67af_notified_emission_tracked))
(assert
 (= c335b67af_notified_emission_untracked c335b67af_notified_emission_untracked))
(assert
 (= c335b67af_voter_total_weight c335b67af_voter_total_weight))
(define-fun report_preconditions () Bool (and (= 0 c335b67af_voter_total_weight) c335b67af_notified_emission_tracked))
(define-fun report_safety () Bool (= c335b67af_notified_emission_recoverable c335b67af_notified_emission_tracked))
(define-fun report_effects () Bool (and c335b67af_notified_emission_tracked
     (not (= c335b67af_notified_emission_recoverable
             c335b67af_notified_emission_tracked))
     c335b67af_notified_emission_untracked
     c335b67af_notified_emission_untracked))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
