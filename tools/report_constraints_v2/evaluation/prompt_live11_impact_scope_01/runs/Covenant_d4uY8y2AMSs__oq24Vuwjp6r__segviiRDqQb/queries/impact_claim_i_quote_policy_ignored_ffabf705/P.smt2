; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4116c220_market_init_reads_base () Bool)
(declare-fun c4116c220_market_no_cap_limit_after_init () Int)
(declare-fun c4116c220_quote_default_configured () Bool)
(declare-fun c4116c220_quote_default_no_cap_limit () Int)
(declare-fun c4116c220_quote_policy_ignored () Bool)
(assert
 (= c4116c220_market_init_reads_base c4116c220_market_init_reads_base))
(assert
 (= c4116c220_market_no_cap_limit_after_init c4116c220_market_no_cap_limit_after_init))
(assert
 (= c4116c220_quote_default_configured c4116c220_quote_default_configured))
(assert
 (= c4116c220_quote_default_no_cap_limit c4116c220_quote_default_no_cap_limit))
(assert
 (= c4116c220_quote_policy_ignored c4116c220_quote_policy_ignored))
(define-fun report_preconditions () Bool (and c4116c220_quote_default_configured c4116c220_market_init_reads_base))
(define-fun report_safety () Bool (=> (and c4116c220_quote_default_configured c4116c220_market_init_reads_base)
    (and (= c4116c220_market_no_cap_limit_after_init
            c4116c220_quote_default_no_cap_limit)
         (not c4116c220_quote_policy_ignored))))
(define-fun report_effects () Bool (and c4116c220_quote_default_configured
     c4116c220_market_init_reads_base
     (not (and (= c4116c220_market_no_cap_limit_after_init
                  c4116c220_quote_default_no_cap_limit)
               (not c4116c220_quote_policy_ignored)))))
(assert report_preconditions)
(check-sat)
(get-model)
